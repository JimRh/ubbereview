"""
    Title: EncryptedMessage Model
    Description: This file will contain functions for EncryptedMessage Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models.fields import BinaryField

from api.models.base_table import BaseTable
from api.utilities import security


class EncryptedMessage(BaseTable):
    """
        EncryptedMessage Model
        NOTE: This class should NOT be directly instantiated. Rather, the encrypt_message helper should be used.
    """
    nonce = BinaryField(
        max_length=16,
        editable=False,
        help_text='Created based on data secret key. '
                  'Changing this value or the secret key WILL result in unusable data.'
    )
    header = BinaryField(
        max_length=16,
        editable=False,
        help_text='Created based on data secret key. '
                  'Changing this value or the secret key WILL result in unusable data.'
    )
    ciphertext = BinaryField(
        max_length=255,
        editable=False,
        help_text='Created based on data secret key. '
                  'Changing this value or the secret key WILL result in unusable data.'
    )
    tag = BinaryField(
        max_length=16,
        editable=False,
        help_text='Created based on data secret key. '
                  'Changing this value or the secret key WILL result in unusable data.'
    )

    @staticmethod
    def encrypt_message(message: str) -> 'EncryptedMessage':
        """
            Encrypt a message and store it in an EncryptedMessage object.
            NOTE: this object will NOT be committed to the database.
            Caller should call save method on return if this is desired.
            :param message: message to be encrypted
            :return: uncommitted EncryptedMessage object
        """
        nonce, header, ciphertext, tag = security.encrypt(message)
        return EncryptedMessage(nonce=nonce, header=header, ciphertext=ciphertext, tag=tag)

    def decrypt(self) -> str:
        """
            Encrypt the message represented by an EncryptedMessage
            :return:
        """
        data = {k: getattr(self, k) for k in ('nonce', 'header', 'ciphertext', 'tag')}
        return security.decrypt(**data)

    def __repr__(self):
        return f'< EncryptedMessage({self.nonce}, {self.header}, {self.ciphertext}, {self.tag}) >'

    def __str__(self):
        return 'Encrypted message'

    def save(self, *args, **kwargs) -> None:
        self.clean_fields()
        super().save(*args, **kwargs)
