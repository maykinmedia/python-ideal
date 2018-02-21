# -*- encoding: utf8 -*-
import os

from unittest2 import TestCase

from ideal.security import Security
from ideal.utils import render_to_string


class SecurityTests(TestCase):
    maxDiff = None

    def setUp(self):
        self.security = Security()

        base_filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'mock_certs'))

        self.cert_filepath = os.path.join(base_filepath, 'cert.cer')
        self.pair_filepath = os.path.join(base_filepath, 'pair.p12')
        self.priv_filepath = os.path.join(base_filepath, 'priv.pem')

        self.unsigned_message = """<DirectoryReq xmlns="http://www.idealdesk.com/ideal/messages/mer-acq/3.3.1" version="3.3.1">
    <createDateTimestamp>2013-08-03T11:48:11Z</createDateTimestamp>
    <Merchant>
        <merchantID>001234567</merchantID>
        <subID>0</subID>
    </Merchant>
</DirectoryReq>"""

    def test_get_fingerprint(self):
        """
        Test the XML message KeyName value (or fingerprint).
        """
        expected_fingerprint = '132df198e31e4443e228da75c9299dded61aef10'
        fingerprint = self.security.get_fingerprint(self.cert_filepath)

        self.assertEqual(expected_fingerprint, fingerprint)

    def test_get_message_digest(self):
        """
        Test the XML message DigestValue.
        """
        expected_message_digest = 'Z61204hpQi+arvC1/3u78POWh2IcAGsPnjfla+2AcTc='
        message_digest = self.security.get_message_digest(self.unsigned_message)

        self.assertEqual(expected_message_digest, message_digest)

    def test_get_signature(self):
        """
        Test the XML message SignatureValue.
        """
        message_digest = self.security.get_message_digest(self.unsigned_message)
        signed_info = render_to_string('templates/signed_info.xml', {
            'digest_value': message_digest
        })

        expected_signature = (
            """hmsonk9o7QMUlrVyewEC7+u76I7dy4S4aIuno9/Sj2J7Okfv0XUsGd2Sw7YU7zRy3yKdpHhbtMFt"""
            """QhEsqm/eFBnzd1M+JpdUpAW60vBfa/lQ/RnwX6mBjl3r2vxhUVd3T8BFnnmh5qQ74AjvCYZ6eFXs"""
            """rq4w6b1v+IQZHknC7qQeWX56VDuTv6ezZ4nnAIr2jL//xv3iaOsYRrSK0jRVU6cJyXqhkKEvIQHK"""
            """FkOnJZt7BfQbMQ5goqbqdL3UI+U98bj/1/PTVDxYBvyK26YltX6X3tNB1ovI61BdxMXD/P35mvIq"""
            """2fUJ3IeL0CGw1Epo34na9VtO7+tyIzedfysjUg==""")

        signature = self.security.get_signature(signed_info, self.priv_filepath, 'example')

        self.assertEqual(expected_signature, signature)

    def test_sign_message(self):
        """
        Test signing a message.
        """
        unsigned_msg_body, unsigned_msg_closing = self.unsigned_message.rsplit('<', 1)
        unsigned_msg_closing = '<' + unsigned_msg_closing
        message_digest = self.security.get_message_digest(self.unsigned_message)
        signed_info = render_to_string('templates/signed_info.xml', {'digest_value': message_digest})
        signature = self.security.get_signature(signed_info, self.priv_filepath, 'example')
        fingerprint = self.security.get_fingerprint(self.cert_filepath)

        expected_signed_message = """{msg_body}<Signature xmlns='http://www.w3.org/2000/09/xmldsig#'>
{signed_info}
 <SignatureValue>{signature_value}</SignatureValue>
 <KeyInfo>
   <KeyName>{key_name}</KeyName>
  </KeyInfo>
</Signature>{msg_closing}""".format(
            msg_body=unsigned_msg_body,
            signed_info=signed_info,
            signature_value=signature,
            key_name=fingerprint,
            msg_closing=unsigned_msg_closing
        )

        signed_message = self.security.sign_message(
            self.unsigned_message, self.cert_filepath, self.priv_filepath, 'example')

        self.assertEqual(expected_signed_message, signed_message)

    def test_verify(self):
        """
        Test verify a signed message.
        """
        signed_message = self.security.sign_message(
            self.unsigned_message, self.cert_filepath, self.priv_filepath, 'example')

        # NOTE: Normally, you would want to verify if a response came from the acquirer (ie. ideal_v3.cer) but for
        # testing we simply use our own dummy certificate.
        result = self.security.verify(signed_message, [self.cert_filepath])
        self.assertTrue(result)

        # The verify method supports unicode/str and bytestrings
        signed_message = signed_message.encode('utf-8')
        result = self.security.verify(signed_message, [self.cert_filepath])
        self.assertTrue(result)
