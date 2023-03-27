import uuid

from django.test import TestCase

from api.models import Account, SubAccount, Address, Contact, Markup


class SubAccountTests(TestCase):
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
        self.subaccount_data = {
            'client_account': Account.objects.first(),
            'address': Address.objects.first(),
            'contact': Contact.objects.first(),
            'markup': Markup.objects.first()
        }

    def test_default(self):
        subaccount = SubAccount(**self.subaccount_data)
        self.assertIsInstance(subaccount, SubAccount)
        self.assertIsNone(subaccount.subaccount_number)
        self.assertFalse(subaccount.is_default)

    def test_default_str(self):
        subaccount = SubAccount(**self.subaccount_data)
        self.assertEqual(str(subaccount), 'KenCar')

    def test_default_repr(self):
        subaccount = SubAccount(**self.subaccount_data)
        self.assertEqual(repr(subaccount), '< SubAccount (None) >')

    def test_alternate_is_default(self):
        self.subaccount_data['is_default'] = False
        subaccount = SubAccount(**self.subaccount_data)
        self.assertIsInstance(subaccount, SubAccount)
        self.assertIsNone(subaccount.subaccount_number)
        self.assertFalse(subaccount.is_default)

    def test_alternate_subaccount_number(self):
        self.subaccount_data['subaccount_number'] = uuid.uuid4()
        subaccount = SubAccount(**self.subaccount_data)
        self.assertIsInstance(subaccount, SubAccount)
        self.assertIsInstance(subaccount.subaccount_number, uuid.UUID)
        self.assertEqual(subaccount.subaccount_number, self.subaccount_data['subaccount_number'])
        self.assertFalse(subaccount.is_default)

    def test_save(self):
        subaccount = SubAccount(**self.subaccount_data)
        subaccount.save()
        self.assertIsInstance(subaccount, SubAccount)
        self.assertIsNotNone(subaccount.subaccount_number)
        self.assertFalse(subaccount.is_default)
        self.assertEqual(subaccount.client_account, self.subaccount_data['client_account'])
        self.assertEqual(subaccount.address, self.subaccount_data['address'])
        self.assertEqual(subaccount.contact, self.subaccount_data['contact'])
        self.assertEqual(subaccount.markup, self.subaccount_data['markup'])

    def test_save_alternate_is_default(self):
        self.subaccount_data['is_default'] = False
        subaccount = SubAccount(**self.subaccount_data)
        subaccount.save()
        self.assertIsInstance(subaccount, SubAccount)
        self.assertIsNotNone(subaccount.subaccount_number)
        self.assertFalse(subaccount.is_default)
        self.assertEqual(subaccount.client_account, self.subaccount_data['client_account'])
        self.assertEqual(subaccount.address, self.subaccount_data['address'])
        self.assertEqual(subaccount.contact, self.subaccount_data['contact'])
        self.assertEqual(subaccount.markup, self.subaccount_data['markup'])

    def test_unique_subaccount_number(self):
        self.subaccount_data['subaccount_number'] = uuid.uuid4()
        subaccount = SubAccount(**self.subaccount_data)
        subaccount.save()
        other = SubAccount(**self.subaccount_data)
        self.assertEqual(subaccount.subaccount_number, other.subaccount_number)
        other.save()
        self.assertNotEqual(subaccount.subaccount_number, other.subaccount_number)

    def test_save_maintains_subaccount_number(self):
        self.subaccount_data['subaccount_number'] = uuid.uuid4()
        subaccount = SubAccount(**self.subaccount_data)
        subaccount.save()
        self.assertIsInstance(subaccount, SubAccount)
        number = subaccount.subaccount_number
        subaccount.save()
        self.assertEqual(subaccount.subaccount_number, number)

    def test_saved_str(self):
        subaccount = SubAccount(**self.subaccount_data)
        subaccount.save()
        self.assertEqual(str(subaccount), str(subaccount.contact.company_name))

    def test_saved_repr(self):
        subaccount = SubAccount(**self.subaccount_data)
        subaccount.save()
        self.assertEqual(repr(subaccount), '< SubAccount ({}) >'.format(str(subaccount.subaccount_number)))

    def test_create(self):
        subaccount = SubAccount.create(param_dict=self.subaccount_data)
        self.assertIsInstance(subaccount, SubAccount)
        self.assertEqual(subaccount.markup.name, "Tier Three")
        self.assertEqual(subaccount.contact.name, "KenCar")
        self.assertEqual(subaccount.address.city, "Calgary")
