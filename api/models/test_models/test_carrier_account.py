from django.test import TestCase

from api.models import CarrierAccount, Carrier, EncryptedMessage, SubAccount


class CarrierAccountTests(TestCase):
    fixtures = [
        'carriers',
        "user",
        "group",
        'countries',
        'provinces',
        'addresses',
        'contact',
        'markup',
        'account',
        'subaccount',
        'encryted_messages',
        'carrier_account'
    ]

    def setUp(self):
        encrypted_user = EncryptedMessage.encrypt_message(message="name")
        encrypted_user.save()
        encrypted_pass = EncryptedMessage.encrypt_message(message="name_pass")
        encrypted_pass.save()
        encrypted_con = EncryptedMessage.encrypt_message(message="name_con")
        encrypted_con.save()
        encrypted_key = EncryptedMessage.encrypt_message(message="key")
        encrypted_key.save()
        encrypted_acc = EncryptedMessage.encrypt_message(message="accc")
        encrypted_acc.save()

        self.carrier_account_data = {
            'carrier': Carrier.objects.first(),
            'subaccount': SubAccount.objects.get(pk=1),
            'api_key': encrypted_key,
            'username': encrypted_user,
            'password': encrypted_pass,
            'account_number': encrypted_acc,
            'contract_number': encrypted_con,
        }

    def test_create(self):
        carrier_account = CarrierAccount(**self.carrier_account_data)
        self.assertIsInstance(carrier_account, CarrierAccount)
        carrier_account.save()
        carrier_account = CarrierAccount.objects.get(pk=carrier_account.pk)
        self.assertEqual(carrier_account.carrier, self.carrier_account_data['carrier'])
        self.assertEqual(carrier_account.subaccount, self.carrier_account_data['subaccount'])
        self.assertEqual(carrier_account.api_key, self.carrier_account_data['api_key'])
        self.assertEqual(carrier_account.username, self.carrier_account_data['username'])
        self.assertEqual(carrier_account.password, self.carrier_account_data['password'])
        self.assertEqual(carrier_account.account_number, self.carrier_account_data['account_number'])
        self.assertEqual(carrier_account.contract_number, self.carrier_account_data['contract_number'])

    def test_repr(self):
        carrier_account = CarrierAccount.objects.first()
        self.assertEqual(carrier_account.__repr__(), "< CarrierAccount(subaccount=kenneth carmichael, carrier=Day & Ross) >")

    def test_str(self):
        carrier_account = CarrierAccount.objects.first()
        self.assertEqual(carrier_account.__str__(), "kenneth carmichael, Day & Ross")
