# -*- encoding: utf8 -*-
import datetime
import os
from decimal import Decimal

import dateutil.tz
import mock
from unittest2 import TestCase

from ideal.exceptions import IdealResponseException

from .helpers import MockIdealClient


class ClientTests(TestCase):

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

        # Mock out the verification of responses as they are incorrectly signed. This part is tested in the security
        # test suite.
        self.patcher = mock.patch('ideal.security.Security.verify')
        mock_security_verify = self.patcher.start()
        mock_security_verify.return_value = True

        self.ideal_client = MockIdealClient()

    def tearDown(self):
        self.patcher.stop()

    def test_get_issuers_flat(self):
        """
        Test IdealClient.get_issuers() response and retrieve a flat list of issuers.
        """
        expected_result = {
            'INGBNL2A': 'Issuer Simulation V3 - ING',
            'RABONL2U': 'Issuer Simulation V3 - RABO'
        }

        response = self.ideal_client.get_issuers()
        actual_result = response.get_issuer_list()

        self.assertDictEqual(actual_result, expected_result)

    def test_get_issuers(self):
        """
        Test IdealClient.get_issuers() response and retrieve a country list of issuers.
        """
        expected_result = {
            'Nederland': {
                'INGBNL2A': 'Issuer Simulation V3 - ING',
                'RABONL2U': 'Issuer Simulation V3 - RABO'
            }
        }

        response = self.ideal_client.get_issuers()
        actual_result = response.issuers

        self.assertDictEqual(actual_result, expected_result)

    def test_start_transaction(self):
        """
        Test IdealClient.start_transaction(...) response.
        """
        response = self.ideal_client.start_transaction(
            issuer_id='INGBNL2A',
            purchase_id='test',
            amount=Decimal('1.0'),
            description='test transaction'
        )

        self.assertNotEqual(response.transaction_id, None)
        self.assertTrue(response.transaction_id in response.issuer_authentication_url)
        self.assertNotEqual(response.entrance_code, None)

    def test_get_transaction_status(self):
        """
        Test IdealClient.get_transaction_status(...) response.
        """
        response = self.ideal_client.get_transaction_status(
            transaction_id='0123456789',
        )

        self.assertEqual(response.amount, Decimal('100.00'))
        self.assertEqual(response.consumer_bic, 'INGBNL2A')
        self.assertEqual(response.consumer_iban, 'NL53INGB0654422370')
        self.assertEqual(
            response.consumer_name, u'Hr E G H Küppers en/of Mw M J Küppers an nog een lange consumername')
        self.assertEqual(response.currency, 'EUR')
        self.assertEqual(response.status, 'Success')
        self.assertEqual(
            response.status_date_timestamp, datetime.datetime(2013, 8, 7, 11, 50, 28, 348000, dateutil.tz.tzutc()))
        self.assertEqual(response.transaction_id, '0123456789')

    def test_error(self):
        """
        Test errornous responses from acquirer.
        """
        self.assertRaisesRegexp(IdealResponseException,
                                'IX1100\: Received XML not valid \(Field generating error\: boo\)\.',
                                self.ideal_client._request, '<oops></oops>')
