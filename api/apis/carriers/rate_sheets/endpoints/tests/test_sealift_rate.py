from django.test import TestCase


class SkylineRateV3Tests(TestCase):
    fixtures = [
        "carriers",
        "countries",
        "provinces",
        "addresses",
        "contact",
        "user",
        "group",
        "markup",
        "carrier_markups",
        "account",
        "subaccount",
        "encryted_messages",
        "carrier_account",
    ]
