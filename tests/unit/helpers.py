# -*- encoding: utf8 -*-
import os
from io import open

from ideal.client import IdealClient


class MockIdealClient(IdealClient):
    """
    An Ideal Client that does not communicate with any real acquirer but simply returns predefined responses.
    """
    def _load_example(self, filename):
        filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'mock_responses', filename))

        f = open(filepath)
        result = f.read()
        f.close()

        return result.encode("utf-8")

    def _request(self, data):
        """
        Swap out the actual request and return a mock responses.
        """
        request = self.create_request(data)

        mapping = {
            'DirectoryReq': 'ideal_directory_response.xml',
            'AcquirerTrxReq': 'ideal_transaction_response.xml',
            'AcquirerStatusReq': 'ideal_transaction_status_response.xml',
        }

        response_content = None
        for request_type, response_file in mapping.items():
            if request_type in data:
                response_content = self._load_example(response_file)
                break

        if response_content is None:
            response_content = self._load_example('ideal_error_response.xml')

        return self.create_response({'Server': 'Mock Ideal Server'}, response_content, 200, request)
