Python iDEAL
============

Implementation of the iDEAL v3.1.1 specification in Python.

Quick start
===========

It is assumed you have already requested access at your bank for iDEAL.

1. Install this library in your virtual environment.

2. Generate or locate your certificates (``cert.cer``, ``pair.p12`` and ``priv.pem``) and your bank's public certificate
   (``ideal_v3.cer``), and place them in a folder where your web application can access them.

3. Create a config file called ``ideal.cfg`` (or copy and modify the ``ideal-example.cfg``)::

    [ideal]
    debug = 1
    private_key_file = priv.pem
    private_key_password = secret
    private_certificate = cert.cer
    certificates = ideal_v3.cer
    merchant_id = 123456789
    sub_id = 0
    expiration_period = PT15M
    merchant_return_url = https://www.example.com/ideal/callback/
    vendor = ING
    language = nl

4. In Python, make sure your settings are initialized by loading the config file::

    from ideal.conf import settings
    settings.load('ideal.cfg')

    # You may adjust (or completely define) your settings (capitalized) in Python as well
    settings.DEBUG = True

5. After your settings are loaded, you can communicate with iDEAL::

    from ideal.client import IdealClient
    ideal = IdealClient()

    response = ideal.get_issuers()
    print response.issuers


Contrib
=======

Django
------

1. All settings can be prefixed with ``IDEAL_`` and placed in Django's ``settings.py`` file, rather than using a
   configuration file.

2. Add ``ideal.contrib.django`` to your ``INSTALLED_APPS``.

3. Optionally, you can add the the following to your main ``urls.py`` to test your configuration and perform all iDEAL
   operations via a web interface::

    if settings.DEBUG:
        urlpatterns += patterns('',
            (r'^ideal/tests/', include('ideal.contrib.django.test_urls')),
        )

4. If you are in DEBUG mode and use ``runserver``, you can point your browser to:
   ``http://localhost:8000/ideal/tests/``.
