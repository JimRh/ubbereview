"""
    Title: Webhook Model Unit Tests
    Description: This file will contain all unit tests for webhooks Model.
    Created: July 12, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.core.exceptions import ValidationError
from django.test import TestCase

from api.models import Webhook, SubAccount


class WebhookTests(TestCase):

    fixtures = [
        "carriers",
        "countries",
        "provinces",
        "user",
        "group",
        "contact",
        "addresses",
        "markup",
        "account",
        "subaccount"
    ]

    def setUp(self):
        self.sub_account = SubAccount.objects.first()

        self.webhook_json = {
            "sub_account": self.sub_account,
            "event": "TSC",
            "url": "https://www.ubbe.com/",
            "data_format": "JSO"
        }

    def test_create_empty(self):
        record = Webhook.create()
        self.assertIsInstance(record, Webhook)

    def test_create_full(self):
        record = Webhook.create(self.webhook_json)
        self.assertIsInstance(record, Webhook)
        self.assertEqual(record.event, "TSC")
        self.assertEqual(record.url, "https://www.ubbe.com/")
        self.assertEqual(record.data_format, "JSO")

    def test_set_values(self):
        record = Webhook.create()
        record.set_values(self.webhook_json)
        self.assertIsInstance(record, Webhook)
        self.assertEqual(record.event, "TSC")
        self.assertEqual(record.url, "https://www.ubbe.com/")
        self.assertEqual(record.data_format, "JSO")

    def test_all_fields_verbose(self):
        record = Webhook(**self.webhook_json)
        self.assertIsInstance(record, Webhook)
        self.assertEqual(record.event, "TSC")
        self.assertEqual(record.url, "https://www.ubbe.com/")
        self.assertEqual(record.data_format, "JSO")

    def test_repr(self):
        expected = "< Webhook (< SubAccount (8cd0cae7-6a22-4477-97e1-a7ccfbed3e01) >: TSC, https://www.ubbe.com/, JSO) >"
        record = Webhook(**self.webhook_json)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "kenneth carmichael: TSC, https://www.ubbe.com/, JSO"
        record = Webhook(**self.webhook_json)
        self.assertEqual(expected, str(record))

    def test_save(self):

        record = Webhook.create(param_dict=self.webhook_json)
        record.sub_account = self.sub_account

        try:
            record.save()
        except ValidationError as e:
            self.fail(e)

        self.assertIsInstance(record, Webhook)
        self.assertEqual(record.event, "TSC")
        self.assertEqual(record.url, "https://www.ubbe.com/")
        self.assertEqual(record.data_format, "JSO")
