from django.contrib.auth.models import User
from django.test import TestCase

from api.models import Account, Carrier


class AccountTests(TestCase):
    fixtures = [
        "user",
        "group",
        "carriers"
    ]
    groups_json = {
        "subaccounts_allowed": True
    }

    def setUp(self):
        self.groups_json_full = {
            "user": User.objects.get(username="gobox"),
            "carrier": Carrier.objects.get(code=2),
            "subaccounts_allowed": True
        }

    def test_create_empty(self):
        record = Account.create()
        self.assertIsInstance(record, Account)

    def test_create_full(self):
        record = Account.create(self.groups_json)
        self.assertIsInstance(record, Account)

    def test_all_fields_verbose(self):
        record = Account.create(self.groups_json)
        self.assertTrue(record.subaccounts_allowed)

    def test_repr(self):
        expected = "< Account (gobox) >"
        record = Account.create(self.groups_json_full)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "gobox"
        record = Account.create(self.groups_json_full)
        self.assertEqual(expected, str(record))

    def test_save(self):
        groups_json = {
            "user": User.objects.get(pk=3),
            "carrier": Carrier.objects.get(pk=1),
            "subaccounts_allowed": True
        }
        groups = Account.create(groups_json)

        groups.save()
        self.assertIsInstance(Account.objects.get(user__username="gobox"), Account)
        self.assertEqual(Account.objects.get(user__username="gobox").user.username, "gobox")
        self.assertTrue(Account.objects.get(user__username="gobox").subaccounts_allowed)

