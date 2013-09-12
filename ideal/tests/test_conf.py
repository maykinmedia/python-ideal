#-*- encoding: utf8 -*-
import tempfile
import os

from unittest2 import TestCase

from ideal.conf import Settings
from ideal.exceptions import IdealConfigurationException


class ConfTests(TestCase):

    def setUp(self):
        base_filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'mock_certs'))

        self.cert_filepath = os.path.join(base_filepath, 'cert.cer')
        self.pair_filepath = os.path.join(base_filepath, 'pair.p12')
        self.priv_filepath = os.path.join(base_filepath, 'priv.pem')

    def tearDown(self):
        if hasattr(self, '_config_filepath'):
            os.remove(self._config_filepath)

    def _create_config_file(self, **kwargs):
        """
        Helper function to create a temporary config file.

        :param kwargs: List of keyword arguments where they key and value are stored as config entries.

        :return: The config file absolute path.
        """
        fd, filepath = tempfile.mkstemp()
        self._config_filepath = filepath

        f = os.fdopen(fd, 'w')
        f.write('[ideal]\n')
        for k, v in kwargs.items():
            if isinstance(v, list):
                v = ','.join(v)
            f.write('{key} = {value}\n'.format(key=k.lower(), value=v))

        f.close()

        return self._config_filepath

    def _test_settings(self, settings, **kwargs):
        """
        Performs tests to check if the provided ``settings`` object contains the values as provided as ``kwargs``. If an
        option is not provided in the ``kwargs``, the default is checked.

        :param settings: The :class:`Settings` object.
        :param kwargs: List of keyword arguments where they key is the config option, and the value the config value.
        """

        defaults = {
            'ACQUIRER': None,
            'ACQUIRER_URL': None,
            'DEBUG': True,
            'EXPIRATION_PERIOD': 'PT15M',
            'CERTIFICATES': ['ideal_v3.cer'],
            'LANGUAGE': 'nl',
            'MERCHANT_ID': '',
            'MERCHANT_RETURN_URL': '',
            'PRIVATE_CERTIFICATE': 'cert.cer',
            'PRIVATE_KEY_FILE': 'priv.pem',
            'PRIVATE_KEY_PASSWORD': '',
            'SUB_ID': '0',
        }
        
        for k, v in kwargs.items():
            option = k.upper()

            expected_value = getattr(settings, option, defaults[option])

            self.assertEqual(expected_value, v,
                             'Option {option} is {value} but should be {expected}.'.format(option=option, value=v,
                                                                                           expected=expected_value))

    def test_default_config(self):
        """
        Check if the default config is initialized properly.
        """
        settings = Settings()

        self.assertListEqual(settings.options(), ['ACQUIRER', 'ACQUIRER_URL', 'CERTIFICATES', 'DEBUG',
                                                  'EXPIRATION_PERIOD', 'LANGUAGE', 'MERCHANT_ID', 'MERCHANT_RETURN_URL',
                                                  'PRIVATE_CERTIFICATE', 'PRIVATE_KEY_FILE', 'PRIVATE_KEY_PASSWORD',
                                                  'SUB_ID'])

        self._test_settings(settings)

        self.assertRaisesRegexp(IdealConfigurationException,
                                'The MERCHANT_ID setting cannot be empty.', settings.validate)

        self.assertRaisesRegexp(IdealConfigurationException,
                                'Could not get the acquirer URL for ACQUIRER="None".', settings.get_acquirer_url)

    def test_config_from_file(self):
        """
        Test config can be read from file.
        """
        config = {
            'debug': 0,
            'private_key_file': self.priv_filepath,
            'private_key_password': 'example',
            'private_certificate': self.cert_filepath,
            'certificates': [self.cert_filepath],
            'merchant_id': '001234567',
            'sub_id': '0',
            'merchant_return_url': 'https://www.example.com/ideal/callback/',
            'acquirer': 'ING',
        }
        
        config_filepath = self._create_config_file(**config)

        settings = Settings()
        settings.load(config_filepath)

        self._test_settings(settings, **config)

        settings.validate()

    def test_config_manually(self):
        """
        Test manually set configuration parameters.
        """
        config = {
            'debug': False,
            'private_key_file': self.priv_filepath,
            'private_key_password': 'example',
            'private_certificate': self.cert_filepath,
            'certificates': [self.cert_filepath],
            'merchant_id': '001234567',
            'sub_id': '0',
            'merchant_return_url': 'https://www.example.com/ideal/callback/',
            'acquirer': 'ING',
        }

        settings = Settings()

        for k, v in config.items():
            setattr(settings, k.upper(), v)

        self._test_settings(settings, **config)

        settings.validate()

    def test_fixed_acquirer_url(self):
        """
        Test the correct acquirer URL if the setting ACQUIRER_URL is provided.
        """
        settings = Settings()

        settings.ACQUIRER_URL = 'http://www.example.com'

        self.assertEqual(settings.get_acquirer_url(), 'http://www.example.com')
        self.assertEqual(settings.get_acquirer_url(test=False), 'http://www.example.com')
        self.assertEqual(settings.get_acquirer_url(test=True), 'http://www.example.com')

    def test_param_acquirer_url(self):
        """
        Test the correct acquirer URL if the setting ACQUIRER and/or DEBUG is provided.
        """
        settings = Settings()

        settings.DEBUG = False

        self.assertEqual(settings.get_acquirer_url('ING'), settings._ACQUIRERS['ING']['ACQUIRER_URL'])
        self.assertEqual(settings.get_acquirer_url('ING', False), settings._ACQUIRERS['ING']['ACQUIRER_URL'])
        self.assertEqual(settings.get_acquirer_url('ING', True), settings._ACQUIRERS['ING']['ACQUIRER_URL_TEST'])

        settings.DEBUG = True

        self.assertEqual(settings.get_acquirer_url('ING'), settings._ACQUIRERS['ING']['ACQUIRER_URL_TEST'])
        self.assertEqual(settings.get_acquirer_url('ING', False), settings._ACQUIRERS['ING']['ACQUIRER_URL'])
        self.assertEqual(settings.get_acquirer_url('ING', True), settings._ACQUIRERS['ING']['ACQUIRER_URL_TEST'])

    def test_validation(self):
        """
        Test if all validation is performed correctly.
        """
        settings = Settings()

        self.assertRaisesRegexp(IdealConfigurationException,
                                'The MERCHANT_ID setting cannot be empty\.', settings.validate)

        settings.MERCHANT_ID = '001234567'

        self.assertRaisesRegexp(IdealConfigurationException,
                                'The MERCHANT_RETURN_URL setting cannot be empty\.', settings.validate)

        settings.MERCHANT_RETURN_URL = 'https://www.example.com/ideal/callback/'

        self.assertRaisesRegexp(IdealConfigurationException,
                                'The PRIVATE_KEY_PASSWORD setting cannot be empty\.', settings.validate)

        settings.PRIVATE_KEY_PASSWORD = 'example'

        self.assertRaisesRegexp(IdealConfigurationException,
                                'Either ACQUIRER or ACQUIRER_URL needs to set\.', settings.validate)

        settings.ACQUIRER = 'ING'

        self.assertRaisesRegexp(IdealConfigurationException,
                                'The PRIVATE_KEY_FILE file \(priv\.pem\) could not be found\.', settings.validate)

        settings.PRIVATE_KEY_FILE = self.priv_filepath

        self.assertRaisesRegexp(IdealConfigurationException,
                                'The PRIVATE_CERTIFICATE file \(cert\.cer\) could not be found\.', settings.validate)

        settings.PRIVATE_CERTIFICATE = self.cert_filepath

        self.assertRaisesRegexp(IdealConfigurationException,
                                'One of the CERTIFICATES files \(ideal_v3\.cer\) could not be found\.',
                                settings.validate)

        settings.CERTIFICATES = [self.cert_filepath]

        settings.validate()
