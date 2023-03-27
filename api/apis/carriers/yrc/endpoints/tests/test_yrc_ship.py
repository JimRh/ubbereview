"""
    Title: YRC Ship Unit Tests
    Description: Unit Tests for the YRC Ship. Test Everything.
    Created: January 25, 2020
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""
import copy
import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.yrc.endpoints.yrc_ship import YRCShip
from api.globals.carriers import YRC
from api.models import SubAccount, Carrier, CarrierAccount


class YRCShipTests(TestCase):
    fixtures = [
        "api",
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
        "northern_pd",
        "skyline_account",
        "nature_of_goods",
    ]

    def setUp(self):
        sub_account = SubAccount.objects.get(
            subaccount_number="8cd0cae7-6a22-4477-97e1-a7ccfbed3e01"
        )
        user = User.objects.get(username="gobox")
        carrier = Carrier.objects.get(code=YRC)
        carrier_account = CarrierAccount.objects.get(
            subaccount=sub_account, carrier=carrier
        )

        self.request = {
            "origin": {
                "address": "1540 Airport Road",
                "city": "Edmonton International Airport",
                "company_name": "BBE Ottawa",
                "email": "developer@bbex.com",
                "phone": "7809326245",
                "name": "BBE",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB",
                "is_residential": False,
                "has_shipping_bays": True,
            },
            "destination": {
                "address": "140 THAD JOHNSON PRIV Suite 7",
                "city": "Ottawa",
                "company_name": "BBE Ottawa",
                "name": "BBE",
                "email": "developer@bbex.com",
                "phone": "7809326245",
                "country": "CA",
                "postal_code": "K1V0R1",
                "province": "ON",
                "has_shipping_bays": True,
                "is_residential": False,
            },
            "pickup": {
                "date": datetime.datetime.strptime("2021-08-12", "%Y-%m-%d").date(),
                "start_time": "10:00",
                "end_time": "16:00",
            },
            "packages": [
                {
                    "package_type": "SKID",
                    "freight_class": "70.00",
                    "description": "TEST",
                    "quantity": 1,
                    "length": "48",
                    "width": "48",
                    "height": "48",
                    "weight": "100",
                    "imperial_length": Decimal("48"),
                    "imperial_width": Decimal("48"),
                    "imperial_height": Decimal("48"),
                    "imperial_weight": Decimal("100"),
                    "is_dangerous_good": False,
                }
            ],
            "objects": {
                "sub_account": sub_account,
                "user": user,
                "carrier_accounts": {
                    YRC: {"account": carrier_account, "carrier": carrier}
                },
            },
            "carrier_options": [],
            "service_code": "STD|123456786543",
            "order_number": "UB1234567890",
            "is_pickup": True
        }

        self.response_one = {
            "isSuccess": True,
            "referenceIds": ["87380070"],
            "createTS": "2017-07-14T11:58:06-05:00",
            "isWeatherAlert": False,
            "isDirect": True,
        }
        self.response_two = {
            "isSuccess": True,
            "masterId": "87388888",
            "referenceIds": ["87380070", "87380070"],
            "createTS": "2017-07-14T11:58:06-05:00",
            "isWeatherAlert": False,
            "isDirect": True,
        }

        self._yrc_ship = YRCShip(ubbe_request=self.request)

    def test_build_bol_detail(self):
        """
        Test Ship Building of BOL detail section.
        """
        ret = self._yrc_ship._build_bol_detail(pickup_date="08/12/2021")
        expected = {
            "pickupDate": "08/12/2021",
            "role": "TP",
            "autoSchedulePickup": False,
            "autoEmailBOL": False,
            "paymentTerms": "P",
            "originAddressSameAsShipper": True,
        }
        self.assertDictEqual(expected, ret)

    def test_build_bol_detail_two(self):
        """
        Test Ship Building of BOL detail section two.
        """
        ret = self._yrc_ship._build_bol_detail(pickup_date="01/25/2022")
        expected = {
            "pickupDate": "01/25/2022",
            "role": "TP",
            "autoSchedulePickup": False,
            "autoEmailBOL": False,
            "paymentTerms": "P",
            "originAddressSameAsShipper": True,
        }
        self.assertDictEqual(expected, ret)

    def test_build_documents(self):
        """
        Test Ship Building of documents section.
        """
        ret = self._yrc_ship._build_documents()
        expected = {
            "generateBolPDF": True,
            "bolDocumentType": "STD",
            "generateShippingLabelsPDF": True,
            "numberOfLabelsPerShipment": 1,
            "labelStartingPosition": 1,
            "labelFormat": "CONT_4X6",
            "generateProLabelsPDF": False,
        }
        self.assertDictEqual(expected, ret)

    def test_build_third_party(self):
        """
        Test Ship Building of third party section.
        """
        ret = self._yrc_ship._build_third_party()
        expected = {
            "companyName": "BBE Expediting",
            "phoneNumber": "780-890-6811",
            "address": "1759 35 Ave E",
            "city": "Edmonton Intl Airport",
            "state": "AB",
            "zip": "T9E0V6",
            "country": "CAN",
        }
        self.assertDictEqual(expected, ret)

    def test_build_option_value_homp(self):
        """
        Test Ship Building of option value code.
        """
        ret = self._yrc_ship._build_option_value(option_code="HOMP")
        expected = {"serviceOptionType": "HOMP", "serviceOptionPaymentTerms": "P"}
        self.assertDictEqual(expected, ret)

    def test_build_option_value_homd(self):
        """
        Test Ship Building of option value code.
        """
        ret = self._yrc_ship._build_option_value(option_code="HOMD")
        expected = {"serviceOptionType": "HOMD", "serviceOptionPaymentTerms": "P"}
        self.assertDictEqual(expected, ret)

    def test_build_option_value_ip(self):
        """
        Test Ship Building of option value code.
        """
        ret = self._yrc_ship._build_option_value(option_code="IP")
        expected = {"serviceOptionType": "IP", "serviceOptionPaymentTerms": "P"}
        self.assertDictEqual(expected, ret)

    def test_build_option_value_id(self):
        """
        Test Ship Building of option value code.
        """
        ret = self._yrc_ship._build_option_value(option_code="ID")
        expected = {"serviceOptionType": "ID", "serviceOptionPaymentTerms": "P"}
        self.assertDictEqual(expected, ret)

    def test_build_option_value_lfto(self):
        """
        Test Ship Building of option value code.
        """
        ret = self._yrc_ship._build_option_value(option_code="LFTO")
        expected = {"serviceOptionType": "LFTO", "serviceOptionPaymentTerms": "P"}
        self.assertDictEqual(expected, ret)

    def test_build_option_value_lftd(self):
        """
        Test Ship Building of option value code.
        """
        ret = self._yrc_ship._build_option_value(option_code="LFTD")
        expected = {"serviceOptionType": "LFTD", "serviceOptionPaymentTerms": "P"}
        self.assertDictEqual(expected, ret)

    def test_build_option_value_appt(self):
        """
        Test Ship Building of option value code.
        """
        ret = self._yrc_ship._build_option_value(option_code="APPT")
        expected = {"serviceOptionType": "APPT", "serviceOptionPaymentTerms": "P"}
        self.assertDictEqual(expected, ret)

    def test_build_address_origin(self):
        """
        Test Ship Building of address.
        """
        ret = self._yrc_ship._build_address(address=self.request["origin"])
        expected = {
            "companyName": "BBE Ottawa",
            "contactName": "BBE",
            "phoneNumber": "7809326245",
            "address": "1540 Airport Road",
            "city": "edmonton international airport",
            "state": "AB",
            "zip": "T9E0V6",
            "country": "CAN",
        }
        self.assertDictEqual(expected, ret)

    def test_build_address_destination(self):
        """
        Test Ship Building of address.
        """
        ret = self._yrc_ship._build_address(address=self.request["destination"])
        expected = {
            "companyName": "BBE Ottawa",
            "contactName": "BBE",
            "phoneNumber": "7809326245",
            "address": "140 THAD JOHNSON PRIV Suite 7",
            "city": "ottawa",
            "state": "ON",
            "zip": "K1V0R1",
            "country": "CAN",
        }
        self.assertDictEqual(expected, ret)

    def test_build_address_usa(self):
        """
        Test Ship Building of address with us origin
        """
        address = {
            "address": "452 Morse Road",
            "city": "Bennington",
            "company_name": "BBE Ottawa",
            "email": "developer@bbex.com",
            "phone": "7809326245",
            "name": "BBE",
            "country": "US",
            "postal_code": "05201",
            "province": "VT",
            "is_residential": False,
            "has_shipping_bays": True,
        }

        ret = self._yrc_ship._build_address(address=address)
        expected = {
            "companyName": "BBE Ottawa",
            "contactName": "BBE",
            "phoneNumber": "7809326245",
            "address": "452 Morse Road",
            "city": "bennington",
            "state": "VT",
            "zip": "05201",
            "country": "USA",
        }
        self.assertDictEqual(expected, ret)

    def test_build_address_mexico(self):
        """
        Test Ship Building of address with mexico origin
        """
        address = {
            "address": "Predio Paraiso Escondido s/n",
            "city": "Cabo San Lucas",
            "company_name": "BBE Ottawa",
            "email": "developer@bbex.com",
            "phone": "7809326245",
            "name": "BBE",
            "country": "MX",
            "postal_code": "23450",
            "province": "BCS",
            "is_residential": False,
            "has_shipping_bays": True,
        }

        ret = self._yrc_ship._build_address(address=address)
        expected = {
            "companyName": "BBE Ottawa",
            "contactName": "BBE",
            "phoneNumber": "7809326245",
            "address": "Predio Paraiso Escondido s/n",
            "city": "cabo san lucas",
            "state": "BCS",
            "zip": "23450",
            "country": "MEX",
        }
        self.assertDictEqual(expected, ret)

    def test_build_packages(self):
        """
        Test Ship Building of packages section.
        """
        ret = self._yrc_ship._build_packages(packages=self.request["packages"])
        expected = [
            {
                "productDesc": "TEST",
                "handlingUnitQuantity": 1,
                "handlingUnitType": "SKD",
                "length": Decimal("48"),
                "width": Decimal("48"),
                "height": Decimal("48"),
                "totalWeight": Decimal("100"),
                "freightClass": 70,
                "isHazardous": False,
            }
        ]
        self.assertListEqual(expected, ret)

    def test_build_packages_multiple(self):
        """
        Test Ship Building of packages section.
        """
        copied = copy.deepcopy(self.request)
        copied["packages"].append(
            {
                "description": "TEST",
                "package_type": "DRUM",
                "freight_class": "70.00",
                "quantity": 1,
                "length": "48",
                "width": "48",
                "height": "48",
                "weight": "100",
                "imperial_length": Decimal("48"),
                "imperial_width": Decimal("48"),
                "imperial_height": Decimal("48"),
                "imperial_weight": Decimal("100"),
                "is_dangerous_good": False,
            }
        )

        ret = self._yrc_ship._build_packages(packages=copied["packages"])
        expected = [
            {
                "productDesc": "TEST",
                "handlingUnitQuantity": 1,
                "handlingUnitType": "SKD",
                "length": Decimal("48"),
                "width": Decimal("48"),
                "height": Decimal("48"),
                "totalWeight": Decimal("100"),
                "freightClass": 70,
                "isHazardous": False,
            },
            {
                "productDesc": "TEST",
                "handlingUnitQuantity": 1,
                "handlingUnitType": "DRM",
                "length": Decimal("48"),
                "width": Decimal("48"),
                "height": Decimal("48"),
                "totalWeight": Decimal("100"),
                "freightClass": 70,
                "isHazardous": False,
            },
        ]

        self.assertListEqual(expected, ret)

    def test_build_packages_dg(self):
        """
        Test Ship Building of packages section.
        """
        copied = copy.deepcopy(self.request)
        copied["packages"].append(
            {
                "description": "TEST",
                "package_type": "DRUM",
                "freight_class": "70.00",
                "quantity": 1,
                "length": "48",
                "width": "48",
                "height": "48",
                "weight": "100",
                "imperial_length": Decimal("48"),
                "imperial_width": Decimal("48"),
                "imperial_height": Decimal("48"),
                "imperial_weight": Decimal("100"),
                "is_dangerous_good": True,
                "proper_shipping_name": "My DG",
                "un_number": 1234,
                "class_div": "1",
                "packing_group_str": "III",
            }
        )

        ret = self._yrc_ship._build_packages(packages=copied["packages"])
        expected = [
            {
                "productDesc": "TEST",
                "handlingUnitQuantity": 1,
                "handlingUnitType": "SKD",
                "length": 48,
                "width": 48,
                "height": 48,
                "totalWeight": 100,
                "freightClass": 70,
                "isHazardous": False,
            },
            {
                "productDesc": "TEST",
                "handlingUnitQuantity": 1,
                "handlingUnitType": "DRM",
                "length": 48,
                "width": 48,
                "height": 48,
                "totalWeight": 100,
                "freightClass": 70,
                "isHazardous": True,
                "hazmatInfo": {
                    "technicalName": "My DG",
                    "shipmentDescribedPer": "T",
                    "unnaNumber": "UN1234",
                    "hazmatClass": "1",
                    "packagingGroup": "III",
                    "emergency24hrPhone": "(888) 226-8832",
                },
            },
        ]

        self.assertListEqual(expected, ret)

    def test_build_option_homp(self):
        """
        Test Ship Building of option - origin residential.
        """
        copied = copy.deepcopy(self.request)
        copied["origin"]["has_shipping_bays"] = False

        ret = YRCShip(ubbe_request=copied)._build_options(options=[])
        expected = [{"serviceOptionType": "HOMP", "serviceOptionPaymentTerms": "P"}]
        self.assertListEqual(expected, ret)

    def test_build_option_homd(self):
        """
        Test Ship Building of option - destination residential.
        """
        copied = copy.deepcopy(self.request)
        copied["destination"]["has_shipping_bays"] = False

        ret = YRCShip(ubbe_request=copied)._build_options(options=[])
        expected = [{"serviceOptionType": "HOMD", "serviceOptionPaymentTerms": "P"}]
        self.assertListEqual(expected, ret)

    def test_build_option_ip(self):
        """
        Test Ship Building of option - inside pickup.
        """
        ret = self._yrc_ship._build_options(options=[9])
        expected = [{"serviceOptionType": "IP", "serviceOptionPaymentTerms": "P"}]
        self.assertListEqual(expected, ret)

    def test_build_option_id(self):
        """
        Test Ship Building of option - inside delivery.
        """
        ret = self._yrc_ship._build_options(options=[10])
        expected = [{"serviceOptionType": "ID", "serviceOptionPaymentTerms": "P"}]
        self.assertListEqual(expected, ret)

    def test_build_option_lfto(self):
        """
        Test Ship Building of option - tailgate pickup.
        """
        ret = self._yrc_ship._build_options(options=[3])
        expected = [{"serviceOptionType": "LFTO", "serviceOptionPaymentTerms": "P"}]
        self.assertListEqual(expected, ret)

    def test_build_option_lftd(self):
        """
        Test Ship Building of option - tailgate delivery.
        """
        ret = self._yrc_ship._build_options(options=[17])
        expected = [{"serviceOptionType": "LFTD", "serviceOptionPaymentTerms": "P"}]
        self.assertListEqual(expected, ret)

    def test_build_option_appt(self):
        """
        Test Ship Building of option - delivery appointment.
        """
        ret = self._yrc_ship._build_options(options=[1])
        expected = [{"serviceOptionType": "APPT", "serviceOptionPaymentTerms": "P"}]
        self.assertListEqual(expected, ret)

    def test_build_option_multiple(self):
        """
        Test Ship Building of option - delivery appointment.
        """
        ret = self._yrc_ship._build_options(options=[1, 17, 3, 10])
        expected = [
            {"serviceOptionType": "APPT", "serviceOptionPaymentTerms": "P"},
            {"serviceOptionType": "LFTD", "serviceOptionPaymentTerms": "P"},
            {"serviceOptionType": "LFTO", "serviceOptionPaymentTerms": "P"},
            {"serviceOptionType": "ID", "serviceOptionPaymentTerms": "P"},
        ]
        self.assertListEqual(expected, ret)

    def test_build_option_multiple_with_res(self):
        """
        Test Ship Building of option - delivery appointment.
        """

        copied = copy.deepcopy(self.request)
        copied["origin"]["has_shipping_bays"] = False

        ret = YRCShip(ubbe_request=copied)._build_options(options=[1, 17, 3, 10])
        expected = [
            {"serviceOptionType": "HOMP", "serviceOptionPaymentTerms": "P"},
            {"serviceOptionType": "APPT", "serviceOptionPaymentTerms": "P"},
            {"serviceOptionType": "LFTD", "serviceOptionPaymentTerms": "P"},
            {"serviceOptionType": "LFTO", "serviceOptionPaymentTerms": "P"},
            {"serviceOptionType": "ID", "serviceOptionPaymentTerms": "P"},
        ]
        self.assertListEqual(expected, ret)

    def test_build_reference_numbers(self):
        """
        Test Ship Building of option - delivery appointment.
        """
        ret = self._yrc_ship._build_reference_numbers()
        expected = [{"refNumber": "UB1234567890", "refNumberType": "PO"}]
        self.assertListEqual(expected, ret)

    def test_build_reference_numbers_ref_one(self):
        """
        Test Ship Building of option - delivery appointment.
        """
        copied = copy.deepcopy(self.request)
        copied["reference_one"] = "Reference One"

        ret = YRCShip(ubbe_request=copied)._build_reference_numbers()
        expected = [
            {"refNumber": "UB1234567890", "refNumberType": "PO"},
            {"refNumber": "Reference One", "refNumberType": "CO"},
        ]
        self.assertListEqual(expected, ret)

    def test_build_reference_numbers_ref_two(self):
        """
        Test Ship Building of option - delivery appointment.
        """
        copied = copy.deepcopy(self.request)
        copied["reference_two"] = "Reference Two"

        ret = YRCShip(ubbe_request=copied)._build_reference_numbers()
        expected = [
            {"refNumber": "UB1234567890", "refNumberType": "PO"},
            {"refNumber": "Reference Two", "refNumberType": "RN"},
        ]
        self.assertListEqual(expected, ret)

    def test_build_reference_numbers_all(self):
        """
        Test Ship Building of option - delivery appointment.
        """
        copied = copy.deepcopy(self.request)
        copied["reference_one"] = "Reference One"
        copied["reference_two"] = "Reference Two"

        ret = YRCShip(ubbe_request=copied)._build_reference_numbers()
        expected = [
            {"refNumber": "UB1234567890", "refNumberType": "PO"},
            {"refNumber": "Reference One", "refNumberType": "CO"},
            {"refNumber": "Reference Two", "refNumberType": "RN"},
        ]
        self.assertListEqual(expected, ret)

    def test_build_service(self):
        """
        Test Ship Building of service
        """
        ret = self._yrc_ship._build_service(
            service_parts=["STD", "123456786543"],pickup_date=self.request["pickup"]["date"]
        )
        expected = {"deliveryServiceOption": "LTL"}
        self.assertDictEqual(expected, ret)

    def test_build_service_tcsa(self):
        """
        Test Ship Building of service
        """
        copied = copy.deepcopy(self.request)
        copied["service_code"] = "GD|123456786543"

        ret = YRCShip(ubbe_request=copied)._build_service(
            service_parts=["TCSA", "123456786543"],
            pickup_date=self.request["pickup"]["date"]
        )
        expected = {
            "deliveryServiceOption": "GTC",
            "GTCAdditionalInfo": {
                "dueByDate": "08/20/2021",
                "dueByTime": "NOON",
                "GTCproactiveNotification": {
                    "isProActiveNotificationSelected": False,
                    "contactName": "Customer Service",
                    "contactPhone": "888-420-6926",
                },
            },
        }
        self.assertDictEqual(expected, ret)

    def test_build_service_tcsp(self):
        """
        Test Ship Building of service
        """
        copied = copy.deepcopy(self.request)
        copied["service_code"] = "GD|123456786543"

        ret = YRCShip(ubbe_request=copied)._build_service(
            service_parts=["TCSP", "123456786543"],
            pickup_date=self.request["pickup"]["date"]
        )
        expected = {
            "deliveryServiceOption": "GTC",
            "GTCAdditionalInfo": {
                "dueByDate": "08/20/2021",
                "dueByTime": "FIVE_PM",
                "GTCproactiveNotification": {
                    "isProActiveNotificationSelected": False,
                    "contactName": "Customer Service",
                    "contactPhone": "888-420-6926",
                },
            },
        }
        self.assertDictEqual(expected, ret)

    def test_create_request(self):
        """
        Test Ship Building of create request
        """
        ret = self._yrc_ship._create_request()
        expected = {
            "UsernameToken": {"Username": "BBEYZF", "Password": "BBEYZF"},
            "submitBOLRequest": {
                "bolDetail": {
                    "pickupDate": "08/12/2021",
                    "role": "TP",
                    "autoSchedulePickup": False,
                    "autoEmailBOL": False,
                    "paymentTerms": "P",
                    "originAddressSameAsShipper": True,
                },
                "shipper": {
                    "companyName": "BBE Ottawa",
                    "contactName": "BBE",
                    "phoneNumber": "7809326245",
                    "address": "1540 Airport Road",
                    "city": "edmonton international airport",
                    "state": "AB",
                    "zip": "T9E0V6",
                    "country": "CAN",
                },
                "consignee": {
                    "companyName": "BBE Ottawa",
                    "contactName": "BBE",
                    "phoneNumber": "7809326245",
                    "address": "140 THAD JOHNSON PRIV Suite 7",
                    "city": "ottawa",
                    "state": "ON",
                    "zip": "K1V0R1",
                    "country": "CAN",
                },
                "thirdParty": {
                    "companyName": "BBE Expediting",
                    "phoneNumber": "780-890-6811",
                    "address": "1759 35 Ave E",
                    "city": "Edmonton Intl Airport",
                    "state": "AB",
                    "zip": "T9E0V6",
                    "country": "CAN",
                },
                "commodityInformation": {"weightTypeIdentifier": "LB"},
                "commodityItem": [
                    {
                        "productDesc": "TEST",
                        "handlingUnitQuantity": 1,
                        "handlingUnitType": "SKD",
                        "length": 48,
                        "width": 48,
                        "height": 48,
                        "totalWeight": 100,
                        "freightClass": 70,
                        "isHazardous": False,
                    }
                ],
                "referenceNumbers": [
                    {"refNumber": "UB1234567890", "refNumberType": "PO"}
                ],
                "specialInstuctions": {"dockInstructions": "QID: 123456786543, "},
                "deliveryServiceOptions": {"deliveryServiceOption": "LTL"},
                "bolLabelPDF": {
                    "generateBolPDF": True,
                    "bolDocumentType": "STD",
                    "generateShippingLabelsPDF": True,
                    "numberOfLabelsPerShipment": 1,
                    "labelStartingPosition": 1,
                    "labelFormat": "CONT_4X6",
                    "generateProLabelsPDF": False,
                },
            },
        }
        self.assertDictEqual(expected, ret)

    def test_create_request_international(self):
        """
        Test Ship Building of service
        """
        copied = copy.deepcopy(self.request)
        copied["is_international"] = True
        copied["broker"] = {
            "address": "452 Morse Road",
            "city": "Bennington",
            "company_name": "BBE Ottawa",
            "email": "developer@bbex.com",
            "phone": "7809326245",
            "name": "BBE",
            "country": "US",
            "postal_code": "05201",
            "province": "VT",
            "is_residential": False,
            "has_shipping_bays": True,
        }

        ret = YRCShip(ubbe_request=copied)._create_request()
        expected = {
            "UsernameToken": {"Username": "BBEYZF", "Password": "BBEYZF"},
            "submitBOLRequest": {
                "bolDetail": {
                    "pickupDate": "08/12/2021",
                    "role": "TP",
                    "autoSchedulePickup": False,
                    "autoEmailBOL": False,
                    "paymentTerms": "P",
                    "originAddressSameAsShipper": True,
                },
                "shipper": {
                    "companyName": "BBE Ottawa",
                    "contactName": "BBE",
                    "phoneNumber": "7809326245",
                    "address": "1540 Airport Road",
                    "city": "edmonton international airport",
                    "state": "AB",
                    "zip": "T9E0V6",
                    "country": "CAN",
                },
                "consignee": {
                    "companyName": "BBE Ottawa",
                    "contactName": "BBE",
                    "phoneNumber": "7809326245",
                    "address": "140 THAD JOHNSON PRIV Suite 7",
                    "city": "ottawa",
                    "state": "ON",
                    "zip": "K1V0R1",
                    "country": "CAN",
                },
                "thirdParty": {
                    "companyName": "BBE Expediting",
                    "phoneNumber": "780-890-6811",
                    "address": "1759 35 Ave E",
                    "city": "Edmonton Intl Airport",
                    "state": "AB",
                    "zip": "T9E0V6",
                    "country": "CAN",
                },
                "customsBroker": {
                    "companyName": "BBE Ottawa",
                    "contactName": "BBE",
                    "phoneNumber": "7809326245",
                    "address": "452 Morse Road",
                    "city": "bennington",
                    "state": "VT",
                    "zip": "05201",
                    "country": "USA",
                },
                "commodityInformation": {"weightTypeIdentifier": "LB"},
                "commodityItem": [
                    {
                        "productDesc": "TEST",
                        "handlingUnitQuantity": 1,
                        "handlingUnitType": "SKD",
                        "length": 48,
                        "width": 48,
                        "height": 48,
                        "totalWeight": 100,
                        "freightClass": 70,
                        "isHazardous": False,
                    }
                ],
                "referenceNumbers": [
                    {"refNumber": "UB1234567890", "refNumberType": "PO"}
                ],
                "specialInstuctions": {"dockInstructions": "QID: 123456786543, "},
                "deliveryServiceOptions": {"deliveryServiceOption": "LTL"},
                "bolLabelPDF": {
                    "generateBolPDF": True,
                    "bolDocumentType": "STD",
                    "generateShippingLabelsPDF": True,
                    "numberOfLabelsPerShipment": 1,
                    "labelStartingPosition": 1,
                    "labelFormat": "CONT_4X6",
                    "generateProLabelsPDF": False,
                },
            },
        }
        self.assertDictEqual(expected, ret)

    def test_create_request_options(self):
        """
        Test Ship Building of create request
        """
        copied = copy.deepcopy(self.request)
        copied["carrier_options"] = [1, 3]

        ret = YRCShip(ubbe_request=copied)._create_request()
        expected = {
            "UsernameToken": {"Username": "BBEYZF", "Password": "BBEYZF"},
            "submitBOLRequest": {
                "bolDetail": {
                    "pickupDate": "08/12/2021",
                    "role": "TP",
                    "autoSchedulePickup": False,
                    "autoEmailBOL": False,
                    "paymentTerms": "P",
                    "originAddressSameAsShipper": True,
                },
                "shipper": {
                    "companyName": "BBE Ottawa",
                    "contactName": "BBE",
                    "phoneNumber": "7809326245",
                    "address": "1540 Airport Road",
                    "city": "edmonton international airport",
                    "state": "AB",
                    "zip": "T9E0V6",
                    "country": "CAN",
                },
                "consignee": {
                    "companyName": "BBE Ottawa",
                    "contactName": "BBE",
                    "phoneNumber": "7809326245",
                    "address": "140 THAD JOHNSON PRIV Suite 7",
                    "city": "ottawa",
                    "state": "ON",
                    "zip": "K1V0R1",
                    "country": "CAN",
                },
                "thirdParty": {
                    "companyName": "BBE Expediting",
                    "phoneNumber": "780-890-6811",
                    "address": "1759 35 Ave E",
                    "city": "Edmonton Intl Airport",
                    "state": "AB",
                    "zip": "T9E0V6",
                    "country": "CAN",
                },
                "commodityInformation": {"weightTypeIdentifier": "LB"},
                "commodityItem": [
                    {
                        "productDesc": "TEST",
                        "handlingUnitQuantity": 1,
                        "handlingUnitType": "SKD",
                        "length": 48,
                        "width": 48,
                        "height": 48,
                        "totalWeight": 100,
                        "freightClass": 70,
                        "isHazardous": False,
                    }
                ],
                "referenceNumbers": [
                    {"refNumber": "UB1234567890", "refNumberType": "PO"}
                ],
                "specialInstuctions": {"dockInstructions": "QID: 123456786543, "},
                "deliveryServiceOptions": {"deliveryServiceOption": "LTL"},
                "bolLabelPDF": {
                    "generateBolPDF": True,
                    "bolDocumentType": "STD",
                    "generateShippingLabelsPDF": True,
                    "numberOfLabelsPerShipment": 1,
                    "labelStartingPosition": 1,
                    "labelFormat": "CONT_4X6",
                    "generateProLabelsPDF": False,
                },
                "serviceOptions": [
                    {"serviceOptionType": "APPT", "serviceOptionPaymentTerms": "P"},
                    {"serviceOptionType": "LFTO", "serviceOptionPaymentTerms": "P"},
                ],
            },
        }
        self.assertDictEqual(expected, ret)

    def test_create_request_options_international(self):
        """
        Test Ship Building of create request
        """
        copied = copy.deepcopy(self.request)
        copied["carrier_options"] = [1, 3]
        copied["is_international"] = True
        copied["broker"] = {
            "address": "452 Morse Road",
            "city": "Bennington",
            "company_name": "BBE Ottawa",
            "email": "developer@bbex.com",
            "phone": "7809326245",
            "name": "BBE",
            "country": "US",
            "postal_code": "05201",
            "province": "VT",
            "is_residential": False,
            "has_shipping_bays": True,
        }

        ret = YRCShip(ubbe_request=copied)._create_request()
        expected = {
            "UsernameToken": {"Username": "BBEYZF", "Password": "BBEYZF"},
            "submitBOLRequest": {
                "bolDetail": {
                    "pickupDate": "08/12/2021",
                    "role": "TP",
                    "autoSchedulePickup": False,
                    "autoEmailBOL": False,
                    "paymentTerms": "P",
                    "originAddressSameAsShipper": True,
                },
                "shipper": {
                    "companyName": "BBE Ottawa",
                    "contactName": "BBE",
                    "phoneNumber": "7809326245",
                    "address": "1540 Airport Road",
                    "city": "edmonton international airport",
                    "state": "AB",
                    "zip": "T9E0V6",
                    "country": "CAN",
                },
                "consignee": {
                    "companyName": "BBE Ottawa",
                    "contactName": "BBE",
                    "phoneNumber": "7809326245",
                    "address": "140 THAD JOHNSON PRIV Suite 7",
                    "city": "ottawa",
                    "state": "ON",
                    "zip": "K1V0R1",
                    "country": "CAN",
                },
                "thirdParty": {
                    "companyName": "BBE Expediting",
                    "phoneNumber": "780-890-6811",
                    "address": "1759 35 Ave E",
                    "city": "Edmonton Intl Airport",
                    "state": "AB",
                    "zip": "T9E0V6",
                    "country": "CAN",
                },
                "customsBroker": {
                    "companyName": "BBE Ottawa",
                    "contactName": "BBE",
                    "phoneNumber": "7809326245",
                    "address": "452 Morse Road",
                    "city": "bennington",
                    "state": "VT",
                    "zip": "05201",
                    "country": "USA",
                },
                "commodityInformation": {"weightTypeIdentifier": "LB"},
                "commodityItem": [
                    {
                        "productDesc": "TEST",
                        "handlingUnitQuantity": 1,
                        "handlingUnitType": "SKD",
                        "length": 48,
                        "width": 48,
                        "height": 48,
                        "totalWeight": 100,
                        "freightClass": 70,
                        "isHazardous": False,
                    }
                ],
                "referenceNumbers": [
                    {"refNumber": "UB1234567890", "refNumberType": "PO"}
                ],
                "specialInstuctions": {"dockInstructions": "QID: 123456786543, "},
                "deliveryServiceOptions": {"deliveryServiceOption": "LTL"},
                "bolLabelPDF": {
                    "generateBolPDF": True,
                    "bolDocumentType": "STD",
                    "generateShippingLabelsPDF": True,
                    "numberOfLabelsPerShipment": 1,
                    "labelStartingPosition": 1,
                    "labelFormat": "CONT_4X6",
                    "generateProLabelsPDF": False,
                },
                "serviceOptions": [
                    {"serviceOptionType": "APPT", "serviceOptionPaymentTerms": "P"},
                    {"serviceOptionType": "LFTO", "serviceOptionPaymentTerms": "P"},
                ],
            },
        }
        self.assertDictEqual(expected, ret)
