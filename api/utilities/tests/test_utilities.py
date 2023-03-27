from base64 import b64encode

from Crypto.Random import get_random_bytes
from django.test import TestCase

from api.utilities import security
from brain import settings


class TestEncryption(TestCase):
    message = 'Secret'

    def setUp(self):
        settings.DATA_KEY = b64encode(get_random_bytes(256)).decode('ascii')

    def test_encrypt_decrypt(self):
        self.assertEqual(security.decrypt(*security.encrypt(self.message)), self.message)

    def altered_nonce(self):
        nonce, header, ciphertext, tag = security.encrypt(self.message)
        nonce = b'asdf'
        with self.assertRaises(ValueError):
            security.decrypt(nonce, header, ciphertext, tag)

    def altered_header(self):
        nonce, header, ciphertext, tag = security.encrypt(self.message)
        header = b'asdf'
        with self.assertRaises(ValueError):
            security.decrypt(nonce, header, ciphertext, tag)

    def altered_ciphertext(self):
        nonce, header, ciphertext, tag = security.encrypt(self.message)
        ciphertext = b'asdf'
        with self.assertRaises(ValueError):
            security.decrypt(nonce, header, ciphertext, tag)

    def altered_tag(self):
        nonce, header, ciphertext, tag = security.encrypt(self.message)
        tag = b'asdf'
        with self.assertRaises(ValueError):
            security.decrypt(nonce, header, ciphertext, tag)
