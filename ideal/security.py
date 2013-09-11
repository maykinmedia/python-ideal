import re
import os
import hashlib
import base64
import logging
from io import BytesIO

import M2Crypto
from lxml import etree

from ideal.utils import render_to_string, IDEAL_NAMESPACES


logger = logging.getLogger(__name__)


class Security(object):
    def get_fingerprint(self, private_certificate):
        """
        Return the certificate SHA1-fingerprint.

        :param private_certificate: File path to the merchant's own certificate file (ie. cert.cer).

        :return: Fingerprint as a string.
        """
        cert = M2Crypto.X509.load_cert(private_certificate)
        fingerprint = cert.get_fingerprint('sha1')

        del cert

        # Fill the fingerprint with zero's upto 40 chars.
        return fingerprint.zfill(40).lower()

    def get_message_digest(self, msg, digest_method=None):
        """
        Return the message digeset of given ``msg`` using ``digest_method`` as hashing function.

        :param msg: The message to create a digest of.
        :param digest_method: The hashing function to use, as string (optional). Default\: 'sha256'.

        :return: Base 64 encoded message digest.
        """
        if digest_method is None:
            digest_method = 'sha256'

        digest_func = getattr(hashlib, digest_method.split('#')[-1])
        return base64.b64encode(digest_func(msg).digest())

    def get_signature(self, signed_info, private_key, password):
        """
        Return a signature for the ``signed_info`` string, using provided ``private_key`` and ``password`` to unlock the
        private key.

        :param signed_info: The XML snippet containing only the signed info part as string.
        :param private_key: File path to the Merchant's private key file.
        :param password: Password to unlock the ``private_key``.

        :return: Base 64 encoded signature.
        """

        if type(signed_info) == unicode:
            signed_info = signed_info.encode('utf-8')

        signed_info_tree = etree.parse(BytesIO(signed_info))
        f = BytesIO()
        signed_info_tree.write_c14n(f, exclusive=True)
        signed_info_str = f.getvalue()

        key = M2Crypto.EVP.load_key(private_key, lambda x: password)
        key.reset_context('sha256')

        key.sign_init()
        key.sign_update(signed_info_str)

        signature = key.sign_final()

        del key

        return signature.encode('base64').rstrip('\n')

    def sign_message(self, msg, private_certificate, private_key, password):
        """
        Return the signed message.

        :param msg: The unsigned XML message to sign.
        :param private_certificate: File path to the Merchant's certificate file.
        :param private_key: File path to the Merchant's private key file.
        :param password: Password to unlock the ``private_key``.

        :return: The signed message.
        """
        signed_info = render_to_string('templates/signed_info.xml', {
            'digest_value': self.get_message_digest(msg)
        })

        signature = render_to_string('templates/signature.xml', {
            'signed_info': signed_info,
            'signature_value': self.get_signature(signed_info, private_key, password),
            'key_name': self.get_fingerprint(private_certificate),
        })

        content, container_end = msg.rsplit('<', 1)

        return ''.join([content, signature, '<', container_end])

    def verify(self, xml_document, certificates):
        """
        Return ``True`` if the ``xml_document`` can be verified against any of the ``certificates``.

        :param xml_document: The XML document, as string, to verify.
        :param certificates: List of certificates. Any certificate may match to return a positive result.

        :return: ``True``, if verification succeded. ``False`` otherwise.
        """
        if type(xml_document) == unicode:
            xml_document = xml_document.encode('utf-8')

        xml_tree = etree.parse(BytesIO(xml_document))

        signature = xml_tree.xpath('xmldsig:Signature', namespaces=IDEAL_NAMESPACES)[0]
        signed_info = signature.xpath('xmldsig:SignedInfo', namespaces=IDEAL_NAMESPACES)[0]

        # Remove the signature, strip the XML header and strip trailing newlines.
        unsigned_xml = re.sub(re.compile('<\?.*\?>\n?|<Signature.*</Signature>', flags=re.DOTALL), '', xml_document).rstrip('\n')

        digest_method = signed_info.xpath('xmldsig:Reference/xmldsig:DigestMethod',
                namespaces=IDEAL_NAMESPACES)[0].get('Algorithm')

        digest_value = signed_info.xpath('xmldsig:Reference/xmldsig:DigestValue',
                namespaces=IDEAL_NAMESPACES)[0].text

        # Verify message digest: Signature should be about the unsigned XML.
        if digest_value != self.get_message_digest(unsigned_xml, digest_method):
            return False

        # Get signature properties.
        c14n_method = signed_info.xpath('xmldsig:CanonicalizationMethod',
                namespaces=IDEAL_NAMESPACES)[0].get('Algorithm')
        signature_method = signed_info.xpath('xmldsig:SignatureMethod',
                namespaces=IDEAL_NAMESPACES)[0].get('Algorithm')
        transforms = [el.get('Algorithm') for el in
                signed_info.xpath('xmldsig:Reference/xmldsig:Transforms/xmldsig:Transform',
                namespaces=IDEAL_NAMESPACES)]

        signature_value = signature.xpath('xmldsig:SignatureValue', namespaces=IDEAL_NAMESPACES)[0].text
        key_name = signature.xpath('xmldsig:KeyInfo/xmldsig:KeyName', namespaces=IDEAL_NAMESPACES)[0].text

        # Apply canonicalization.
        signed_info_tree = etree.ElementTree(signed_info)
        f = BytesIO()
        signed_info_tree.write_c14n(f, exclusive=(c14n_method == 'http://www.w3.org/2001/10/xml-exc-c14n#'))
        signed_info_str = f.getvalue()

        # TODO: Apply transformations (currently not needed).

        # Go through the list of installed certificates.
        for cert_file in certificates:
            # Match the given XML signature's fingerprint (KeyName) with the fingerprints of one of the installed
            # certificates.
            if key_name.lower() == self.get_fingerprint(cert_file):

                # Verify signature.
                certificate = M2Crypto.X509.load_cert(cert_file)
                public_key = certificate.get_pubkey()

                # TODO: Use the signature (or message digest?) method for verification (currently using sha256).
                public_key.reset_context(md='sha256')
                public_key.verify_init()
                public_key.verify_update(signed_info_str)

                result = public_key.verify_final(signature_value.decode('base64'))
                del certificate, public_key

                return result == 1

        return False
