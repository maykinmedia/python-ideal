from lxml.etree import QName

from ideal.utils import IDEAL_NAMESPACES


class IdealException(Exception):
    pass


class IdealConfigurationException(IdealException):
    pass


class IdealSecurityException(IdealException):
    pass


class IdealServerException(IdealException):
    pass


class IdealResponseException(IdealException):
    error_code = None
    error_message = None
    error_detail = None
    suggested_action = None
    consumer_message = None

    def __init__(self, xml_document):

        self._xml_document = xml_document

        mapping = {
            'errorCode': 'error_code',
            'errorMessage': 'error_message',
            'errorDetail': 'error_detail',
            'suggestedAction': 'suggested_action',
            'consumerMessage': 'consumer_message'
        }

        for node in xml_document.xpath('//ideal:Error/*', namespaces=IDEAL_NAMESPACES):
            tag_name = QName(node.tag).localname
            if tag_name in mapping:
                setattr(self, mapping[tag_name], node.text)

    @property
    def message(self):
        return '{code}: {message} ({detail}).'.format(code=self.error_code, message=self.error_message,
                                                      detail=self.error_detail)

    def __str__(self):
        return self.message
