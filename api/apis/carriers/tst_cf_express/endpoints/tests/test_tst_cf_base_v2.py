import copy
from decimal import Decimal

from django.test import TestCase

from lxml import etree

from api.apis.carriers.tst_cf_express.endpoints.tst_cf_base_v2 import TstCfExpressApi
from api.models import Carrier, CarrierAccount, SubAccount


class TstCfExpressApiTests(TestCase):
    fixtures = [
        "api",
        "carriers",
        "user",
        "group",
        "account",
        "countries",
        "provinces",
        "addresses",
        "contact",
        "markup",
        "subaccount",
        "encryted_messages",
        "carrier_account",
    ]

    def setUp(self):
        sub_account = SubAccount.objects.get(
            subaccount_number="8cd0cae7-6a22-4477-97e1-a7ccfbed3e01"
        )
        carrier = Carrier.objects.get(code=129)
        carrier_cccount = CarrierAccount.objects.get(
            subaccount=sub_account, carrier=carrier
        )

        self._request = {
            "account_number": "8cd0cae7-6a22-4477-97e1-a7ccfbed3e01",
            "pickup": {
                "start_time": "08:00",
                "date": "2020-05-14",
                "end_time": "16:30",
            },
            "origin": {
                "company_name": "TESTING INC",
                "name": "TESTING INC TWO",
                "email": "developer@bbex.com",
                "phone": "7809326245",
                "address": "140 Thad Johnson Private 7",
                "city": "Edmonton",
                "country": "CA",
                "province": "AB",
                "postal_code": "T5T4R7",
                "has_shipping_bays": True,
            },
            "destination": {
                "address": "140 Thad Johnson Road",
                "city": "Ottawa",
                "company_name": "KENNETH CARMICHAEL",
                "country": "CA",
                "postal_code": "K1V0R4",
                "province": "ON",
                "name": "TESTING INC TWO",
                "email": "developer@bbex.com",
                "phone": "7809326245",
                "has_shipping_bays": True,
            },
            "packages": [
                {
                    "width": Decimal("11"),
                    "package_type": "BOX",
                    "quantity": 1,
                    "length": Decimal("11"),
                    "package": 1,
                    "description": "TEST",
                    "height": Decimal("11"),
                    "weight": Decimal("46"),
                    "imperial_length": Decimal("4.33"),
                    "imperial_width": Decimal("4.33"),
                    "imperial_height": Decimal("4.33"),
                    "imperial_weight": Decimal("101.41"),
                    "is_dangerous_good": False,
                    "volume": Decimal("0.001331"),
                    "is_last": True,
                }
            ],
            "reference_one": "SOMEREF TEST",
            "reference_two": "SOMEREF TEST",
            "is_food": False,
            "is_metric": True,
            "bc_fields": {"bc_job_number": "J00034", "bc_username": "SKIP"},
            "total_pieces": Decimal("1"),
            "total_weight": Decimal("46.00"),
            "total_volume": Decimal("1331.00"),
            "total_weight_imperial": Decimal("101.41"),
            "total_volume_imperial": Decimal("0.05"),
            "is_international": False,
            "is_dangerous_shipment": False,
            "objects": {
                "sub_account": "",
                "carrier_accounts": {
                    129: {"account": carrier_cccount, "carrier": carrier}
                },
            },
            "is_bbe": False,
            "api_client_email": "developer@bbex.com",
            "carrier_id": 129,
            "carrier_name": "TST Overland",
            "carrier_email": "developer@bbex.com",
            "service_code": "G1-1125240",
            "dg_service": None,
            "order_number": "ub2490233447M",
            "carrier_options": [],
        }

        self.tst_base = TstCfExpressApi(ubbe_request=self._request)

    def test_add_child_str_value(self):
        """
        Test Add Child element.
        """
        record = self.tst_base._add_child(element="test", value="string")

        self.assertIsInstance(record, etree._Element)
        self.assertEqual(record.tag, "test")
        self.assertEqual(record.text, "string")

    def test_add_child_bad_int(self):
        """
        Test Add Child invalid value
        """

        with self.assertRaises(TypeError) as e:
            record = self.tst_base._add_child(element="test", value=1)

        self.assertEqual(
            "Argument must be bytes or unicode, got 'int'", str(e.exception)
        )

    def test_add_auth(self):
        """
        Test adding auth to request element
        """
        request = etree.Element("test")
        self.tst_base._add_auth(request=request)

        self.assertIsInstance(request, etree._Element)
        self.assertIsInstance(request[0], etree._Element)
        self.assertEqual(request[0].tag, "requestor")
        self.assertEqual(request[0].text, "BBEXPD")
        self.assertIsInstance(request[1], etree._Element)
        self.assertEqual(request[1].tag, "authorization")
        self.assertEqual(request[1].text, "14gl32ab2pisaal3vck34pxm3ijh91ad")
        self.assertIsInstance(request[2], etree._Element)
        self.assertEqual(request[2].tag, "login")
        self.assertEqual(request[2].text, "Expediting@bbex.com")
        self.assertIsInstance(request[3], etree._Element)
        self.assertEqual(request[3].tag, "passwd")
        self.assertEqual(request[3].text, "Expediting")

    def test_build_options_empty(self):
        """
        Test build tst options empty.
        """

        options = self.tst_base._build_options()

        self.assertIsInstance(options, etree._Element)
        self.assertEqual(options.tag, "accitems")

    def test_build_options_origin_residential(self):
        """
        Test build tst options origin residential.
        """
        copied = copy.deepcopy(self._request)
        copied["origin"]["has_shipping_bays"] = False

        options = TstCfExpressApi(ubbe_request=copied)._build_options()

        self.assertIsInstance(options, etree._Element)
        self.assertEqual(options.tag, "accitems")
        self.assertIsInstance(options[0], etree._Element)
        self.assertEqual(options[0].tag, "item")
        self.assertEqual(options[0].text, "PRP")

    def test_build_options_destination_residential(self):
        """
        Test build tst options destination residential.
        """
        copied = copy.deepcopy(self._request)
        copied["destination"]["has_shipping_bays"] = False

        options = TstCfExpressApi(ubbe_request=copied)._build_options()

        self.assertIsInstance(options, etree._Element)
        self.assertEqual(options.tag, "accitems")
        self.assertIsInstance(options[0], etree._Element)
        self.assertEqual(options[0].tag, "item")
        self.assertEqual(options[0].text, "PRD")

    def test_build_options_appointment(self):
        """
        Test build tst options appointment.
        """
        copied = copy.deepcopy(self._request)
        copied["carrier_options"] = [2]

        options = TstCfExpressApi(ubbe_request=copied)._build_options()

        self.assertIsInstance(options, etree._Element)
        self.assertEqual(options.tag, "accitems")
        self.assertIsInstance(options[0], etree._Element)
        self.assertEqual(options[0].tag, "item")
        self.assertEqual(options[0].text, "APT")

    def test_build_options_inside_pickup(self):
        """
        Test build tst options inside pickup.
        """
        copied = copy.deepcopy(self._request)
        copied["carrier_options"] = [9]

        options = TstCfExpressApi(ubbe_request=copied)._build_options()

        self.assertIsInstance(options, etree._Element)
        self.assertEqual(options.tag, "accitems")
        self.assertIsInstance(options[0], etree._Element)
        self.assertEqual(options[0].tag, "item")
        self.assertEqual(options[0].text, "INSPU")

    def test_build_options_inside_delivery(self):
        """
        Test build tst options inside pickup.
        """
        copied = copy.deepcopy(self._request)
        copied["carrier_options"] = [10]

        options = TstCfExpressApi(ubbe_request=copied)._build_options()

        self.assertIsInstance(options, etree._Element)
        self.assertEqual(options.tag, "accitems")
        self.assertIsInstance(options[0], etree._Element)
        self.assertEqual(options[0].tag, "item")
        self.assertEqual(options[0].text, "INSD")

    def test_build_options_heated_truck(self):
        """
        Test build tst options inside pickup.
        """
        copied = copy.deepcopy(self._request)
        copied["carrier_options"] = [6]

        options = TstCfExpressApi(ubbe_request=copied)._build_options()

        self.assertIsInstance(options, etree._Element)
        self.assertEqual(options.tag, "accitems")
        self.assertIsInstance(options[0], etree._Element)
        self.assertEqual(options[0].tag, "item")
        self.assertEqual(options[0].text, "HEAT")

    def test_build_options_refrigerated_truck(self):
        """
        Test build tst options inside pickup.
        """
        copied = copy.deepcopy(self._request)
        copied["carrier_options"] = [5]

        options = TstCfExpressApi(ubbe_request=copied)._build_options()

        self.assertIsInstance(options, etree._Element)
        self.assertEqual(options.tag, "accitems")
        self.assertIsInstance(options[0], etree._Element)
        self.assertEqual(options[0].tag, "item")
        self.assertEqual(options[0].text, "PSC")

    def test_build_options_power_tailgate_pickup(self):
        """
        Test build tst options inside pickup.
        """
        copied = copy.deepcopy(self._request)
        copied["carrier_options"] = [3]

        options = TstCfExpressApi(ubbe_request=copied)._build_options()

        self.assertIsInstance(options, etree._Element)
        self.assertEqual(options.tag, "accitems")
        self.assertIsInstance(options[0], etree._Element)
        self.assertEqual(options[0].tag, "item")
        self.assertEqual(options[0].text, "TGPU")

    def test_build_options_power_tailgate_delivery(self):
        """
        Test build tst options inside pickup.
        """
        copied = copy.deepcopy(self._request)
        copied["carrier_options"] = [17]

        options = TstCfExpressApi(ubbe_request=copied)._build_options()

        self.assertIsInstance(options, etree._Element)
        self.assertEqual(options.tag, "accitems")
        self.assertIsInstance(options[0], etree._Element)
        self.assertEqual(options[0].tag, "item")
        self.assertEqual(options[0].text, "TGDL")
