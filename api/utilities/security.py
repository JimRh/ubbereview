from base64 import b64decode
from typing import Union, Tuple

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from brain import settings


def encrypt(data: Union[str, bytes]) -> Tuple[bytes, bytes, bytes, bytes]:
    """
    Encrypt a message using AES GCM, using a key and header based on the Django secret key
    :param data: message to encrypt
    :return: tuple of nonce, header, ciphertext, tag
    """
    secret_key = b64decode(settings.DATA_KEY)
    header = get_random_bytes(16)
    if not isinstance(data, bytes):
        data = data.encode()

    cipher = AES.new(secret_key[:16], AES.MODE_GCM)
    cipher.update(header)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return cipher.nonce, header, ciphertext, tag


def decrypt(nonce, header, ciphertext, tag) -> str:
    """
    Decrypt a message using AES GCM
    :param nonce: nonce as returned from encrypt()
    :param header: header as returned from encrypt()
    :param ciphertext: ciphertext as returned from encrypt()
    :param tag: tag as returned from encrypt()
    :return: decrypted message as plaintext
    """
    secret_key = b64decode(settings.DATA_KEY)
    cipher = AES.new(secret_key[:16], AES.MODE_GCM, nonce=nonce)
    cipher.update(header)
    return cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')
