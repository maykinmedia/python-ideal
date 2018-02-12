from django.core.management.base import BaseCommand

from ideal.client import IdealClient
from ideal.contrib.django.ideal_compat.models import Issuer


class Command(BaseCommand):
    help = 'Synchronizes iDEAL issuers with your local database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Performs the command but does not update the database.',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        verbosity = int(options.get('verbosity', 1))

        create_count = update_count = deactivate_count = 0

        ideal = IdealClient()
        response = ideal.get_issuers()

        for country, issuer_list in response.issuers.items():
            for code, name in issuer_list.items():
                if dry_run:
                    is_created = Issuer.objects.filter(code=code).count() == 0
                else:
                    issuer, is_created = Issuer.objects.get_or_create(code=code, defaults={
                        'name': name, 'country': country, 'is_active': True
                    })

                    # Update existing issuer.
                    if not is_created:
                        issuer.name = name
                        issuer.country = country
                        issuer.is_active = True
                        issuer.save()

                if verbosity >= 2:
                    self.stdout.write('{action} issuer ({code}): {name}{dry_run}'.format(
                        action='Created' if is_created else 'Updated',
                        code=code,
                        name=name,
                        dry_run=' (dry-run)' if dry_run else '',
                    ))

                if is_created:
                    create_count += 1
                else:
                    update_count += 1

        # Make all issuers, that were not part of the response, inactive.
        active_issuer_codes = response.get_issuer_list().keys()
        if not dry_run:
            Issuer.objects.exclude(code__in=active_issuer_codes).update(is_active=False)

        if verbosity >= 2:
            for issuer in Issuer.objects.exclude(code__in=active_issuer_codes):
                self.stdout.write('Deactivated issuer ({code}): {name}{dry_run}'.format(
                    code=issuer.code,
                    name=issuer.name,
                    dry_run=' (dry-run)' if dry_run else '',
                ))
                deactivate_count += 1

        if verbosity >= 1:
            self.stdout.write(
                'Issuers: {created} created, {updated} updated, {deactivated} deactivated{dry_run}'.format(
                    created=create_count,
                    updated=update_count,
                    deactivated=deactivate_count,
                    dry_run=' (dry-run)' if dry_run else '',
                )
            )
