from base64 import b64encode
from Crypto.Random import get_random_bytes
from django.test import TestCase

from api.models import EncryptedMessage
from brain import settings


class EncryptedMessageTests(TestCase):
    def setUp(self):
        settings.DATA_KEY = b64encode(get_random_bytes(256)).decode('ascii')
        self.message = 'secret'

    def test_encrypted_message(self):
        e = EncryptedMessage.encrypt_message(self.message)
        self.assertIsInstance(e, EncryptedMessage)
        e.save()
        f = EncryptedMessage.objects.get(pk=1)
        self.assertEqual(f.nonce, e.nonce)
        self.assertEqual(f.ciphertext, e.ciphertext)
        self.assertEqual(f.header, e.header)
        self.assertEqual(f.tag, e.tag)

    def test_decrypt(self):
        e = EncryptedMessage.encrypt_message(self.message)
        self.assertEqual(e.decrypt(), self.message)

    def test_altered_nonce(self):
        e = EncryptedMessage.encrypt_message(self.message)
        e.nonce = b'asdf'
        with self.assertRaises(ValueError):
            e.decrypt()

    def test_altered_ciphertext(self):
        e = EncryptedMessage.encrypt_message(self.message)
        e.ciphertext = b'asdf'
        with self.assertRaises(ValueError):
            e.decrypt()

    def test_altered_header(self):
        e = EncryptedMessage.encrypt_message(self.message)
        e.header = b'asdf'
        with self.assertRaises(ValueError):
            e.decrypt()

    def test_altered_tag(self):
        e = EncryptedMessage.encrypt_message(self.message)
        e.tag = b'asdf'
        with self.assertRaises(ValueError):
            e.decrypt()

    def test_altered_key(self):
        e = EncryptedMessage.encrypt_message(self.message)
        settings.DATA_KEY = 'asdf'
        with self.assertRaises(ValueError):
            e.decrypt()
