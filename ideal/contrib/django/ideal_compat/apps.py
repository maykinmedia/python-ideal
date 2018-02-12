from django.apps import AppConfig
from django.conf import settings as django_settings

from ideal.conf import settings


class IdealConfig(AppConfig):
    name = 'ideal.contrib.django.ideal_compat'

    def ready(self):
        initialize_settings()


def initialize_settings():
    # By default, take Django's DEBUG setting. However, it can be overriden by defining IDEAL_DEBUG in Django's
    # settings.
    settings.DEBUG = django_settings.DEBUG

    for setting_name in settings.options():
        django_setting_value = getattr(django_settings, 'IDEAL_{setting}'.format(setting=setting_name), None)
        if django_setting_value:
            setattr(settings, setting_name, django_setting_value)
