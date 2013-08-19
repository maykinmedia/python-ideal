import os
import ConfigParser

from ideal.exceptions import IdealConfigurationException


class Settings(object):

    PRIVATE_KEY_FILE = 'priv.pem'
    PRIVATE_KEY_PASSWORD = ''
    PRIVATE_CERTIFICATE = 'cert.cer'
    CERTIFICATES = ['ideal_v3.cer',]
    MERCHANT_ID = ''
    SUB_ID = '0'

    # The time the consumer gets to complete the payment.
    EXPIRATION_PERIOD = 'PT15M'  # ISO 8601, minimum is 1 minute, maximum is 1 hour.

    MERCHANT_RETURN_URL = ''

    # The merchant's bank. See VENDORS for valid values.
    ACQUIRER = None

    # The language of messages in the response.
    LANGUAGE = 'nl'  # ISO 639-1, only Dutch (nl) and English (en) are supported.

    DEBUG = True

    _ACQUIRERS = {
        'ING': {
            'ACQUIRER_URL': 'https://ideal.secure-ing.com:443/ideal/iDEALv3',
            'ACQUIRER_URL_TEST': 'https://idealtest.secure-ing.com:443/ideal/iDEALv3',
        }
    }

    def get_acquirer_url(self, acquirer=None, test=None):
        """
        Return the acquirer URL, depending on the ``vendor`` and whether it should be the ``test`` environment or not.

        :param acquirer: Name of the acquirer.
        :param test: ``True`` if the test environment should be used, ``False`` otherwise. Default\: ``settings.DEBUG``.

        :return: The URL of the acquirer's iDEAL environment.
        """
        if acquirer is None:
            acquirer = self.ACQUIRER
        if test is None:
            test = self.DEBUG

        if not acquirer or not test:
            raise IdealConfigurationException(
                'Could not get the acquirer URL for ACQUIRER="{acquirer}".'.format(acquirer=acquirer)
            )

        return self._ACQUIRERS[acquirer]['ACQUIRER_URL%s' % '_TEST' if test else '']

    def options(self):
        """
        Return all available options in the settings.

        :return: List of setting names.
        """
        return [var for var in dir(self) if not var.startswith('_') and not callable(getattr(settings, var))]

    def load(self, config_file):
        """
        Initialize the settings with a config file.

        :param config_file: Configuration file. The section ``[ideal]`` should contain all options.
        """

        config = ConfigParser.ConfigParser()
        config.read(config_file)

        for setting_name in self.options():
            config_setting_name = setting_name.lower()

            if config.has_option('ideal', config_setting_name):
                if setting_name == 'DEBUG':
                    config_setting_value = config.getboolean('ideal', config_setting_name)
                else:
                    config_setting_value = config.get('ideal', config_setting_name)

                if setting_name == 'CERTIFICATES':
                    config_setting_value = [opt.strip() for opt in config_setting_value.split(',')]

                setattr(self, setting_name, config_setting_value)


settings = Settings()
