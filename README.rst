============
Python iDEAL
============

:Version: 0.3.0
:Download: https://pypi.python.org/pypi/ideal
:Source: https://github.com/maykinmedia/python-ideal
:Keywords: python, ideal, django

|build-status| |coverage| |license| |pyversion|

About
=====

Implementation of the iDEAL v3.3.1 specification in Python.

Installation
============

You can install `ideal` either via the Python Package Index (PyPI) or from
source.

To install using ``pip``:

.. code-block:: console

    $ pip install -U ideal

Usage
=====

It is assumed you have already requested access at your bank for iDEAL.

#. Install the `ideal` library:

   .. code-block:: console

      $ pip install ideal

#. Generate or locate your certificates (``cert.cer``, and ``priv.pem``) and your bank's public certificate (here named
   ``ideal_v3.cer`` but depends on your bank), and place them in a folder where your web application can access them.

#. Create a config file called ``ideal.cfg`` (or copy and modify the ``ideal-example.cfg``)::

    [ideal]
    debug = 1
    private_key_file = priv.pem
    private_key_password = secret
    private_certificate = cert.cer
    certificates = ideal_v3.cer
    merchant_id = 123456789
    sub_id = 0
    merchant_return_url = https://www.example.com/ideal/callback/
    acquirer = ING

4. In Python, make sure your settings are initialized by loading the config file:

   .. code-block:: python

    from ideal.conf import settings
    settings.load('ideal.cfg')

    # You may adjust (or completely define) your settings (capitalized) in Python as well
    settings.DEBUG = True

5. After your settings are loaded, you can communicate with iDEAL:

   .. code-block:: python

    from ideal.client import IdealClient
    ideal = IdealClient()

    response = ideal.get_issuers()
    print response.issuers


Settings
========

These settings are lower-case and stored in your ``ideal.cfg`` file (or in Django's ``settings.py``, prefixed with
``IDEAL_``).

*DEBUG* (``boolean``)
    Uses the test URL of the acquirer if set to ``True``, otherwise the production URL is used (default: ``True``).

*PRIVATE_KEY_FILE* (``string``)
    Absolute path to the merchant's private key (default: ``priv.pem``).

*PRIVATE_KEY_PASSWORD* (``string``)
    Password to access the merchant's private key.

*PRIVATE_CERTIFICATE* (``string``)
    Absolute path to the merchant's private certificate (default: ``cert.cer``).

*CERTIFICATES* (``list`` or comma-separated ``string`` if file config is used)
    Absolute path the the acquirer's iDEAL certificate (default: ``ideal_v3.cer``).

*MERCHANT_ID* (``string``)
    The ID of the online shop, received by the acceptor during the iDEAL registration process.

*SUB_ID* (``string``)
    Sub ID of the online shop, also received during the registration process (default: ``0``).

*MERCHANT_RETURN_URL* (``string``)
    The callback URL for iDEAL. The customer is redirected to this URL after the payment process at the acquirer.

*EXPIRATION_PERIOD* (``string``)
    The time a transaction is valid for in ISO 8601 format, minimum is 1 minute, maximum is 1 hour
    (default: ``PT15M``).

*ACQUIRER* (``string``)
    Acquirer code to identify the endpoint. Valid values are: [``ING``, ``RABOBANK``] (default: ``None``).

*ACQUIRER_URL* (``string``)
    Overrides the default acquirer URL and ignores the ``ACQUIRER`` and ``DEBUG`` setting (default: ``None``).

*LANGUAGE* (``string``)
    Response language in ISO 639-1 format, only Dutch (``nl``) and English (``en``) are supported (default: ``nl``).


Testing
=======

To run all unit tests, download the entire package and run:

.. code-block:: console

    $ python setup.py test


Contrib
=======

Django
------

1. All settings can be capitalized and prefixed with ``IDEAL_`` and placed in Django's ``settings.py`` file, rather
   than using a configuration file. Of course, you may still use the settings file method.

2. Add ``ideal.contrib.django.ideal_compat`` to your ``INSTALLED_APPS``.

3. Run ``python manage.py migrate`` to create the ``Issuer`` table in your database, to store a local
   copy of all issuers.

4. Run ``python manage.py sync_issuers`` to fill the ``Issuer`` table with a list of issuers.  You should run this
   command every day or so using a cronjob.

5. You should create a view to handle the iDEAL callback and add the URL (as defined in your settings as
   ``MERCHANT_RETURN_URL``) to your ``urls.py``. Below, you'll find an example view to redirect the use depending on
   the transaction status:

   .. code-block:: python

    from django.views.generic.base import RedirectView
    from ideal.client import IdealClient, TransactionStatus
    from ideal.exceptions import IdealException

    class IdealCallbackView(RedirectView):
        permanent = False

        def get_redirect_url(self, **kwargs):
            """
            Simplistic view to handle the callback. You probably want to update your database with the transaction
            status as well, or sent a confirmation email, etc.
            """
            client = IdealClient()

            try:
                response = client.get_transaction_status(self.request.GET.get('trxid'))
                if response.status == TransactionStatus.SUCCESS:
                    # Redirect to some view with a success message.
                    return '<payment success url>'
            except IdealException, e:
                # Do something with the error message.
                error_message = e.message

            # Redirect to some view with a failure message.
            return '<payment failed url>'

6. Optionally, you can add the the following to your main ``urls.py`` to test your configuration and perform all iDEAL
   operations via a web interface:

   .. code-block:: python

    if settings.DEBUG:
        urlpatterns += [
            url(r'^ideal/tests/', include('ideal.contrib.django.ideal_compat.test_urls')),
        ]

7. If you are in DEBUG mode and use ``runserver``, you can point your browser to:
   ``http://localhost:8000/ideal/tests/``.


.. |build-status| image:: https://secure.travis-ci.org/maykinmedia/python-ideal.svg?branch=master
    :alt: Build status
    :target: https://travis-ci.org/maykinmedia/python-ideal

.. |coverage| image:: https://codecov.io/github/maykinmedia/python-ideal/coverage.svg?branch=master
    :target: https://codecov.io/github/maykinmedia/python-ideal?branch=master

.. |license| image:: https://img.shields.io/pypi/l/ideal.svg
    :alt: MIT License
    :target: https://opensource.org/licenses/MIT

.. |pyversion| image:: https://img.shields.io/pypi/pyversions/ideal.svg
    :alt: Supported Python versions
    :target: http://pypi.python.org/pypi/python-ideal/
