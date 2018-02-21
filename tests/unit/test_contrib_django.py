# -*- encoding: utf8 -*-
from __future__ import unicode_literals

import os

import mock
from django.core.management import call_command
from django.test import override_settings
from django_webtest import WebTest

from ideal.contrib.django.ideal_compat.models import Issuer
from ideal.contrib.django.ideal_compat.utils import reverse

from .helpers import MockIdealClient


@override_settings(DEBUG=True)
class ContribDjangoTestCase(WebTest):
    def setUp(self):
        from ideal.conf import settings

        base_filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'mock_certs'))

        settings.DEBUG = True
        settings.MERCHANT_ID = '001234567'
        settings.PRIVATE_KEY_PASSWORD = 'example'
        settings.ACQUIRER = 'ING'
        settings.MERCHANT_RETURN_URL = 'http://www.example.com/ideal/callback/'
        settings.PRIVATE_KEY_FILE = os.path.join(base_filepath, 'priv.pem')
        settings.PRIVATE_CERTIFICATE = os.path.join(base_filepath, 'cert.cer')
        settings.CERTIFICATES = [os.path.join(base_filepath, 'cert.cer')]

        settings.validate()

        # Mock out the entire IdealClient.
        self.ideal_client_patcher = mock.patch('ideal.client.IdealClient')
        mock_ideal_client = self.ideal_client_patcher.start()
        mock_ideal_client.side_effect = MockIdealClient

        # Mock out the verification of responses as they are incorrectly signed. This part is tested in the security
        # test suite.
        self.security_verify_patcher = mock.patch('ideal.security.Security.verify')
        mock_security_verify = self.security_verify_patcher.start()
        mock_security_verify.return_value = True

    def tearDown(self):
        self.security_verify_patcher.stop()
        self.ideal_client_patcher.stop()

    def test_index(self):
        response = self.app.get(reverse('ideal_tests_index'))
        self.assertEqual(response.status_code, 200)

    def test_get_issuers(self):
        response = self.app.get(reverse('ideal_tests_get_issuers'))
        self.assertEqual(response.status_code, 200)

        # Actually get a list of issuers (banks)
        form = response.form
        response = form.submit()
        self.assertEqual(response.status_code, 200)

        # Validate the mocked list of issuers
        issuers = [(opt.attrib['value'], opt.text) for opt in response.pyquery('#issuer-id-list option')]
        self.assertSetEqual(set(issuers), set([
            ('INGBNL2A', 'Issuer Simulation V3 - ING'),
            ('RABONL2U', 'Issuer Simulation V3 - RABO'),
        ]))

    def test_start_transaction(self):
        response = self.app.get(reverse('ideal_tests_start_transaction'))
        self.assertEqual(response.status_code, 200)

        # Actually start a transaction with given issuer
        form = response.form
        form['issuer_id'] = 'INGBNL2A'
        form['purchase_id'] = 'my-purchase-id'
        form['amount'] = '10.00'
        form['description'] = 'test transaction'
        response = form.submit()
        self.assertEqual(response.status_code, 200)

        # Validate the response
        result = [el.text for el in response.pyquery('#response td')][:3]
        self.assertListEqual(result, [
            # Acquirer ID:
            '0050',
            # Transaction ID:
            '0123456789',
            # Issuer Authentication URL:
            'https://idealtest.secure-ing.com/ideal/issuerSim.do?trxid=0123456789&ideal=prob',
            # Entrance Code:
            # '65a69b128ab53f20f45038de22dc9d418362b01d'
        ])

    def test_get_transaction_status(self):
        response = self.app.get(reverse('ideal_tests_get_transaction_status'))
        self.assertEqual(response.status_code, 200)

        # Actually get the transaction status
        form = response.form
        form['transaction_id'] = '0123456789'
        response = form.submit()
        self.assertEqual(response.status_code, 200)

        # Validate the response
        result = [el.text for el in response.pyquery('#response td')]
        self.assertListEqual(result, [
            # Acquirer ID:
            '0050',
            # Acquirer ID:
            '0123456789',
            # Transaction Status:
            'Success',
            # Status date timestamp:
            '2013-08-07T11:50:28.348000+00:00',
            # Consumer Name:
            'Hr E G H Küppers en/of Mw M J Küppers an nog een lange consumername',
            # Consumer IBAN:
            'NL53INGB0654422370',
            # Consumer BIC:
            'INGBNL2A',
            # Amount:
            '100.00',
            # Currency:
            'EUR',
        ])

    def test_sync_issuers(self):
        self.assertEqual(Issuer.objects.count(), 0)

        call_command('sync_issuers')

        self.assertEqual(Issuer.objects.count(), 2)
        issuer_codes = list(Issuer.objects.order_by('code').values_list('code', flat=True))

        self.assertListEqual(issuer_codes, ['INGBNL2A', 'RABONL2U'])

    def test_sync_issuers_dry_run(self):
        self.assertEqual(Issuer.objects.count(), 0)

        call_command('sync_issuers', dry_run=True)

        self.assertEqual(Issuer.objects.count(), 0)
