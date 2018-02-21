import datetime
import hashlib
import logging
import uuid
from decimal import Decimal
from io import BytesIO

import dateutil.parser
import requests
from lxml import etree
from lxml.etree import QName, XMLSyntaxError

from ideal.conf import settings
from ideal.exceptions import IdealResponseException, IdealSecurityException, IdealServerException
from ideal.security import Security
from ideal.utils import IDEAL_NAMESPACES, convert_camelcase, render_to_string

logger = logging.getLogger(__name__)


class HttpRequest(dict):
    """
    Lightweight container for an HTTP request, containing all relevent properties.
    """
    def __init__(self, uri, method, body=None, headers=None):
        """
        :param uri: Absolute URI of the request.
        :param method: The HTTP method.
        :param body: Data passed in the body of the request.
        :param headers: Dictionary of request headers.
        """
        super(HttpRequest, self).__init__()

        self._uri = uri
        self._method = method
        self._body = body

        if headers is None:
            headers = {}

        self._headers = headers

        self.update(dict([(k.title().replace('_', '-'), v) for k, v in headers.items()]))

    @property
    def headers(self):
        """
        Return the actual headers.
        """
        return self._headers

    @property
    def uri(self):
        return self._uri

    @property
    def method(self):
        return self._method

    @property
    def body(self):
        return self._body


class HttpResponse(dict):
    """
    Lightweight container for an HTTP response.

    Contains a convenience property ``xml`` that may contain an :class:`lxml.etree.ElementTree` object, that was
    parsed from the response content.
    """
    xml = None

    def __init__(self, client, response_headers, response_content, status_code, request):
        """
        Create a new :class:HttpResponse` object. All headers can be accessed as if this object were a dictionary.

        :param client: The client object that generated this response.
        :param response_headers: Dictionary containing the response headers.
        :param response_content: All data passed as response.
        :param status_code: The HTTP status code.
        :param request: The original :class:`HttpRequest` object that was used to trigger this response.
        """
        super(HttpResponse, self).__init__()

        self.client = client
        self.headers = response_headers
        self.content = response_content
        self.status_code = status_code
        self.request = request

        # Make headers consistently accessible.
        self.update(dict([(k.title().replace('_', '-'), v) for k, v in response_headers.items()]))


class IdealResponse(object):
    """
    Container for interesting XML values parsed from the original HTTP response.
    """
    def __init__(self, response):
        """
        Create an iDEAL response object from the original HTTP response (:class:`HttpResponse` object). It is assumed
        the response already contains a property ``xml`` with a parsed :class:`lxml.etree.ElementTree`.

        :param response: The original :class:`HttpResponse` object
        """
        self._response = response

        self._parse(response.xml)

    def _parse(self, xml):
        """
        This function should be overridden in subclasses to parse the XML.
        """
        pass


class DirectoryResponse(IdealResponse):
    acquirer_id = None

    _issuers = None

    def _parse(self, xml):
        self.acquirer_id = xml.xpath(
            'ideal:Acquirer/ideal:acquirerID', namespaces=IDEAL_NAMESPACES)[0].text

        result = {}

        for issuer_node in xml.xpath('//ideal:Issuer', namespaces=IDEAL_NAMESPACES):

            issuer_id = issuer_node.xpath('ideal:issuerID', namespaces=IDEAL_NAMESPACES)[0].text
            issuer_name = issuer_node.xpath('ideal:issuerName', namespaces=IDEAL_NAMESPACES)[0].text

            country_name = issuer_node.getparent().xpath('ideal:countryNames', namespaces=IDEAL_NAMESPACES)[0].text
            if country_name not in result:
                result[country_name] = {}
            result[country_name][issuer_id] = issuer_name

        self._issuers = result

    @property
    def issuers(self):
        return self._issuers.copy()

    def get_issuer_list(self):
        """
        Return a flat list of all issuers.

        :return: A flat list of all issuers.
        """
        result = {}
        for issuer in self._issuers.values():
            result.update(issuer)

        return result


class TransactionStatus(object):
    SUCCESS = 'Success'  # Positive result; the payment is guaranteed.
    CANCELLED = 'Cancelled'  # Negative result due to cancellation by Consumer; no payment has been made.
    EXPIRED = 'Expired'  # Negative result due to expiration of the transaction; no payment has been made.
    FAILURE = 'Failure'  # Negative result due to other reasons; no payment has been made.
    OPEN = 'Open'  # Final result not yet known). A new status request is necessary to obtain the status.


class TransactionResponse(IdealResponse):
    acquirer_id = None

    issuer_authentication_url = None
    transaction_id = None

    # Not an actual part of the transaction response.
    entrance_code = None

    def _parse(self, xml):
        self.acquirer_id = xml.xpath(
            'ideal:Acquirer/ideal:acquirerID', namespaces=IDEAL_NAMESPACES)[0].text

        self.issuer_authentication_url = xml.xpath(
            'ideal:Issuer/ideal:issuerAuthenticationURL', namespaces=IDEAL_NAMESPACES)[0].text

        self.transaction_id = xml.xpath(
            'ideal:Transaction/ideal:transactionID', namespaces=IDEAL_NAMESPACES)[0].text


class StatusResponse(IdealResponse):
    acquirer_id = None

    transaction_id = None
    status = None  # Any of the constants in :class:`TransactionStatus`.
    status_date_timestamp = None
    consumer_name = None
    consumer_iban = None
    consumer_bic = None
    amount = None
    currency = None

    def _parse(self, xml):

        self.acquirer_id = xml.xpath(
            'ideal:Acquirer/ideal:acquirerID', namespaces=IDEAL_NAMESPACES)[0].text

        for transaction_node in xml.xpath('ideal:Transaction/*', namespaces=IDEAL_NAMESPACES):
            attr = convert_camelcase(QName(transaction_node).localname)
            val = transaction_node.text

            if attr == 'amount':
                val = Decimal(val)
            elif attr == 'status_date_timestamp':
                val = dateutil.parser.parse(val)

            setattr(self, attr, val)


class IdealClient(object):
    """
    The iDEAL client to communicate with iDEAL.

    All messages are signed before they are sent to the bank's endpoint. All responses are verified against the iDEAL
    certificate(s).
    """
    def __init__(self):
        self.security = Security()

        # All settings should be correct before instantiating a client.
        settings.validate()

    def _get_context(self, **kwargs):
        """
        Return the default context used in every request.

        :param \*\*kwargs: Additional context, or override the defaults (optional).

        :return: Dictionary with the default context, updated with ``kwargs``.
        """
        now = datetime.datetime.now()

        context = {
            'merchant_id': settings.MERCHANT_ID,
            'sub_id': settings.SUB_ID,
            'timestamp': now.strftime('%Y-%m-%dT%H:%M:%S.000Z')  # TODO: now.isoformat() ?
        }
        context.update(kwargs)

        return context

    def create_request(self, body=None):
        """
        Create a request suited for communicating with iDEAL.
        NOTE: All requests are signed.

        :param body: The unsigned data to send.

        :return: A :class:`HttpRequest` object.
        """
        body = self.security.sign_message(
            body, settings.PRIVATE_CERTIFICATE, settings.PRIVATE_KEY_FILE, settings.PRIVATE_KEY_PASSWORD)

        if body and not body.startswith('<?'):
            body = '<?xml version="1.0" encoding="utf-8"?>' + body

        headers = {
            'content-type': 'text/xml; charset="utf-8"'
        }

        uri = settings.get_acquirer_url()

        return HttpRequest(uri, 'POST', body, headers)

    def create_response(self, response_headers, response_content, status_code, request):
        """
        Create a response from all arguments.
        NOTE: All responses are verified.

        :param response_headers: Dictionary of headers in the response.
        :param response_content: All data from the response.
        :param status_code: The HTTP status code.
        :param request: The original :class:`HttpRequest` object.

        :return: A :class:`HttpResponse` object.
        """
        response = HttpResponse(self, response_headers, response_content, status_code, request)

        if response.status_code != 200:
            raise IdealServerException('iDEAL server returned HTTP {status_code}: {message}'.format(
                status_code=response.status_code,
                message=response.content,
            ))

        try:
            xml_document = etree.parse(BytesIO(response.content))
        except XMLSyntaxError as e:
            raise IdealServerException('iDEAL response could not be parsed: {error}'.format(error=e))

        response.xml = xml_document

        if not self.security.verify(response.content, settings.CERTIFICATES):
            raise IdealSecurityException('iDEAL response could not be verified.')

        if xml_document.xpath('count(//ideal:Error)', namespaces=IDEAL_NAMESPACES) > 0:
            raise IdealResponseException(xml_document)

        return response

    def _request(self, data):
        """
        Constructs a :class:`HttpRequest` object, performs the actual request using the ``requests`` library, and
        return a :class:`HttpResponse` object. This function can be easily overridden to mock requests or to replace
        the ``requests`` library with any other library.

        :param data: The stringified payload to send to iDEAL.

        :return: A :class:`HttpResponse` object.
        """
        logger.debug('Creating request with data: %(data)s', {'data': data})

        request = self.create_request(data)

        logger.debug('Performing request: %(request_method)s %(url)s\n%(request_headers)s\n\n%(body)s', {
            'request_method': request.method,
            'url': request.uri,
            'request_headers': '\n'.join(['%s: %s' % (k, v) for k, v in request.headers.items()]),
            'body': request.body,
        })

        raw_response = requests.request(request.method, request.uri, data=request.body, headers=request.headers)

        logger.debug('Recieved response: HTTP %(response_status)s\n%(response_headers)s\n\n%(data)s', {
            'response_status': raw_response.status_code,
            'response_headers': '\n'.join(['%s: %s' % (k, v) for k, v in raw_response.headers.items()]),
            'data': raw_response.content,
        })

        response = self.create_response(raw_response.headers, raw_response.content, raw_response.status_code, request)

        # If logging is set to DEBUG, don't log this. All details are logged in DEBUG level above.
        if logger.level >= logging.INFO:
            logger.info('%(request_method)s %(url)s (HTTP %(response_status)s)', {
                'request_method': request.method,
                'url': request.uri,
                'response_status': response.status_code
            })

        return response

    def get_issuers(self):
        """
        Sends a "DirectoryReq" to iDEAL to retrieve a list of issuers (banks).

        NOTE: The iDEAL documentation indicates you should get a list of issuers (ie. call this function) every time
        you want to show a list of issuers. Cache these issuers locally; they update rarily.

        :return: A :class: `DirectoryResponse` object.
        """
        context = self._get_context()
        data = render_to_string('templates/directory_request.xml', context)

        r = self._request(data)

        return DirectoryResponse(r)

    def start_transaction(self, issuer_id, purchase_id, amount, description, entrance_code=None,
                          merchant_return_url=None, expiration_period=None, language=None):
        """
        Send an "AcquirerTrxReq" to iDEAL, starting the payment process.

        The returned named tuple can be used to store the transaction details but should always be used to redirect the
        customer to their bank's website by using the ``issuer_authentication_url``. The generated ``entrance_code``
        can be used to resume an incomplete transaction process.

        :param issuer_id: The BIC code of the customer's bank. Usually retrieved with ``IdealClient.get_issuers``.
        :param purchase_id: Any string with a maximum of 16 characters to identify the purchase.
        :param amount: Decimal number for the amount of the transaction.
        :param description: Any string with a maximum of 32 characters describing the purchase.
        :param entrance_code: A unique string of 40 characters to continue the payment process (optional).
        :param merchant_return_url: Override the callback URL (optional). Default\: ``settings.MERCHANT_RETURN_URL``.
        :param expiration_period: Override the expiration period (optional). Default: ``settings.EXPIRATION_PERIOD``.
        :param language: Override the language (optional). Default\: ``settings.LANGUAGE``.

        :return: A :class:`TransactionResponse` object.
        """
        if merchant_return_url is None:
            merchant_return_url = settings.MERCHANT_RETURN_URL
        if language is None:
            language = settings.LANGUAGE
        if entrance_code is None:
            entrance_code = hashlib.sha1(
                uuid.uuid4().hex.encode('utf-8')).hexdigest()
        if expiration_period is None:
            expiration_period = settings.EXPIRATION_PERIOD

        try:
            if str(int(expiration_period)) == str(expiration_period):
                expiration_period = 'PT{n}M'.format(expiration_period)
        except ValueError:
            pass

        # Get all required variables for the template.
        context = self._get_context()
        context.update({
            'issuer_id': issuer_id,
            'merchant_return_url': merchant_return_url,
            'purchase_id': purchase_id[0:16],
            'amount': '{amount:.2f}'.format(amount=amount),  # Use period as decimal separator.
            'currency': 'EUR',  # ISO 4217, Only 'EUR' supported.
            'expiration_period': expiration_period,  # ISO 8601, min. is 1 minute, max. is 1 hour (optional).
            'language': language,  # ISO 639-1, only Dutch (nl) and English (en) are supported.
            'description': description[0:32],
            'entrance_code': entrance_code,
        })

        data = render_to_string('templates/transaction_request.xml', context)

        r = self._request(data)

        response = TransactionResponse(r)

        # Not an actual part of the response, but can be generated in this function and made conveniently accessible.
        response.entrance_code = entrance_code

        return response

    def get_transaction_status(self, transaction_id):
        """
        Sends an "AcquirerStatus" request to iDEAL to retrieve the status of given transaction.

        Eventually, the bank should redirect to your ``settings.MERCHANT_RETURN_URL`` (or the overriden value in
        ``IdealClient.start_transaction``). There are at least 2 query string parameters present in this URL: ``trxid``
        and ``ec``.

        :param transaction_id: The value of ``trxid`` query string parameter.

        :return: A :class:`TransactionResponse` object.
        """

        # Get all required variables for the template.
        context = self._get_context()
        context.update({
            'transaction_id': transaction_id,
        })

        data = render_to_string('templates/transaction_status_request.xml', context)

        r = self._request(data)

        return StatusResponse(r)
