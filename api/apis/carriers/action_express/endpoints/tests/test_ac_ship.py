"""
    Title: Action Express Ship Unit Tests
    Description: Unit Tests for the Action Express Ship. Test Everything.
    Created: Sept 08, 2021
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""

from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.action_express.endpoints.ac_ship import ActionExpressShip
from api.models import SubAccount, Carrier, CarrierAccount


class ACShipTests(TestCase):
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
        "taxes",
    ]

    def setUp(self):
        sub_account = SubAccount.objects.get(
            subaccount_number="8cd0cae7-6a22-4477-97e1-a7ccfbed3e01"
        )
        user = User.objects.get(username="gobox")
        carrier = Carrier.objects.get(code=601)
        carrier_account = CarrierAccount.objects.get(
            subaccount=sub_account, carrier=carrier
        )

        self.request = {
            "service_code": "REG",
            "origin": {
                "address": "1540 Airport Road",
                "city": "Edmonton International Airport",
                "company_name": "BBE Ottawa",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB",
                "has_shipping_bays": True,
            },
            "destination": {
                "address": "1540 Airport Road",
                "city": "Edmonton",
                "company_name": "BBE Ottawa",
                "country": "CA",
                "postal_code": "T5T4R7",
                "province": "AB",
                "has_shipping_bays": True,
            },
            "packages": [
                {
                    "quantity": 1,
                    "length": "100",
                    "width": "50",
                    "height": "50",
                    "weight": "50",
                    "package_type": "BOX",
                },
                {
                    "description": "My Awesome Package",
                    "quantity": 1,
                    "length": "28",
                    "width": "21",
                    "height": "33",
                    "weight": "11",
                    "package_type": "BOX",
                },
            ],
            "objects": {
                "sub_account": sub_account,
                "user": user,
                "carrier_accounts": {
                    601: {"account": carrier_account, "carrier": carrier}
                },
            },
            "pickup": {"date": "2021-09-08", "start": "10:00", "end": "16:00"},
        }

        self.response = {
            "Dispatcher": "8f4c92c3-daaa-4643-874d-e7d3fcb717a8",
            "DriverCurrentlyAssigned": "926cd278-c284-4929-9550-774e428772c6",
            "Customer": "bdd21daf-7078-4325-80df-0a95f90eb665",
            "Items": [],
            "Department": None,
            "CustomerContact": None,
            "PriceSet": "a79c8ce0-f59d-4ed2-8fa9-0b114bd21970",
            "CollectionAssignedDriver": "926cd278-c284-4929-9550-774e428772c6",
            "DeliveryAssignedDriver": "926cd278-c284-4929-9550-774e428772c6",
            "CollectionArrivalWindow": {
                "EarliestTime": "2021-09-07T16:13:25",
                "LatestTime": "2021-09-07T16:13:25",
                "Length": "00:00:00",
            },
            "DeliveryArrivalWindow": {
                "EarliestTime": "2021-09-07T16:13:25",
                "LatestTime": "2021-09-07T20:13:25",
                "Length": "04:00:00",
            },
            "CollectionLocation": {
                "Zone": {
                    "ID": "439e60b6-cfe5-47ca-86c7-f3a9a8192dfa",
                    "Name": "WEST",
                    "PostalCodes": "T5S,T5V,T5L,T5M,T5P,T5S 1K8,T5V 1L2,T5V 1T4,T5M 3T5,T5M 3Z2,T5V 1H2,T5V 1C4,T5M 1W3,T5S 1L7,T5M 3W4,T5S 1K3,T5S 2P1,T5V 1H6,T5L 3C2,T5M 3S7,T5M 3B8,T5V 1T2,T5M 3E8,T5L 2R8,T5V 1M7,T5V 1C9,T5M 3R8,T5L 4P5,T5V 1C6,T5M 3N7,T5V 1L1,T5L 2N9,T5M 0H3,T5L 2M7,T5M 1X8,T5V 1J2,T5M 1V5,T5S 1H8,T5S 0A2,T5S 2C8,T5L 3C1,T5S 1K5,T5M 4E6,T5V 0A5,T5S 2K7,T5S 1H1,T5L 2Y4,T5L 5C3,T5L 3H3,T5S 2E4,T5S 1E5,T5V 1A8,T5M 3T3,T5L 0H8,T5S 2H6,T5L 2W4,T5L 2H8,T5L 4L2,T5S 1P4,T5S 2R7,T5L 0C9,T5M 2S4,T5S 2X3,T5L 2Y1,T5S 1R8,T5S 2Y2,T5L 2H7,T5S 1V4,T5M 3V8,T5M 3S5,T5L 3C5,T5M 3X4,T5S 1H7,T5V 0A1,T5L 2H4,T5S 2R9,T5M 2R8,T5M 3B6,T5L 3C4,T5M 3T2,T5S 2V8,T5S 2X2,T5S 1X3,T5L 3C9,T5V 1H8,T5V 1E4,T5S 0B9,T5S 1V3,T5M 1Y1,T5S 2T3,T5S 2W7,T5M 3T7,T5V 1P2,T5V 1G4,T5L 0T4,T5M 1X1,T5M 3S2,T5S 1E8,T5V 1S4,T5M 3V6,T5S 1G3,T5V 1A1,T5V 1B1,T5L 5H2,T5S 2C6,T5M 2S2,T5V 1K4,T5V 1L8,T5V 1K5,T5V 0B6,T5M 1X6,T5S 1J5,T5S 2G6,T5S 1J7,T5V 0A6,T5S 1E7,T5S 0K3,T5S 2N8,T5L 3M6,T5V 1N8,T5V 1R9,T5L 4N8,T5L 2Y3,T5S 1Z9,T5S 1P2,T5L 4X7,T5V 1T3,T5S 1J4,T5S 1E9,T5S 1M4,T5S 2H5,T5M 2S5,T5S 2P4,T5L 4X4,T5M 3V7,T5M 2V8,T5M 3W1,T5L 4Y3,T5S 1H9,T5V 1L9,T5V 1B8,T5S 1W5,T5L 3B2,T5L 2M5,T5M 2W1,T5M 3n7,T5V 1J5,T5M 3N8,T5V 1B2,T5S 1K4,T5V 1L3,T5M 3T8,T5S 0J5,T5L 2P2,T5V 1B5,T5M 1V4,T5S 2M3,T5S 1C1,T5S 1M8,T5S 2K4,T5V 1L6,T5S 2T2,T5S 1R7,T5M 2X3,T5L 4N9,T5S 1J1,T5L 4R3,T5S 1L1,T5S 2M4,T5S 1N7,T5L 2G8,T5M 3W7,T5M 2Z5,T5M 2Y8,T5S 2B9,T5L 4S9,T5M 1Y6,T5L 3B3,T5V 1S1,T5S 2X5,T5S 1M6,T5S 2K5,T5M 3W6,T5V 0C6,T5M 1V8,T5L 3H6,T5M 3V4,T5S 2L6,T5L 4T4,T5V 1C7,T5S 2H1,T5S 1Y8,T5V 1E9,T5S 1M3,T5M 2T9,T5S 1S4,T5M 0X5,T5M 2Z3,T5M 2P5,T5S 1Y2,T5L 1S5,T5M 1T9,T5S 2A5,T5M 3C1,T5S 2K2,T5S 0H1,T5V 1G8,T5S 1M1,T5M 4E8,T5V 1P6,T5M 3P5,T5S 2P5,T5V 1S7,T5V 1H1,T5S 2K9,T5V 1C2,T5S 1G4,T5S 2P8,T5M 3C5,T5S 1X2,T5L 2J6,T5V 1H4,T5L 0N8,T5S 1E6,T5S 1V8,T5V 1E3,T5M 4A9,T5L 4P2,T5S 2T8,T5S 1K2,T5V 1K9,T5S 2X4,T5L 2T2,T5M 2R7,T5S 0B6,T5S 1L3,T5V 1V2,T5L 3M5,T5S 0C3,T5V 1N5,T5S 2W4,T5S 2L2,T5S 1J3,T5S 2V4,T5V 0B7,T5L 2G9,T5M 3R4,T5S 2N9,T5S 0C4,T5M 3P9,T5S 1S7,T5M 3W2,T5V 0B5,T5V 1B7,T5V 1K2,T5S 2S6,T5S 1G2,T5M 2P4,T5V 1V1,T5M 3Z1,T5M 3W3,T5S 2P2,T5S 2S4,T5M 3N6,T5S 1X8,T5M 3S8,T5S 1T8,T5V 1B3,T5M 0X2,T5V 1E1,T5V 1T9,T5S 2W2,T5S 0A6,T5M 2V9,T5L 4N1,T5S 2R3,T5S 2T4,T5V 1P7,T5M 4C6,T5S 1R5,T5V 1K6,T5L 2J7,T5M 3Z6,T5L 3H5,T5L 0A4,T5M 2X2,T5S 1Y1,T5L 2G5,T5L 2H5,T5S 2L5,T5V 1J7,T5M 1W8,T5S 0A1,T5M 3G1,T5V 1A5,T5M 2Z4,T5M 2Z2,T5M 1Y3,T5M 3B9,T5M 2Z1,T5M 3Y7,T5M3T4,T5V 1G6,T5M 3T4,T5S 1P1,T5V 0C4,T5S 1G7,T5S 2V5,T5V 1J3,T5S 2W3,T5V 1P4,T5M 1X3,T5L 2H2,T5S 2J1,T5S 2V6,T5M 3S1,T5M 3E9,T5L 1C8,T5M 1W9,T5S 2L7,T5M 3S9,T5S 2P6,T5M 3Y3,T5L 4W8,T5V 1C8,T5S 1Z1,T5V 0B4,T5M 3B7,T5V 0A3,T5V 1N4,T5V 1M3,T5L 0X7,T5S 0A8,T5L 4N5,T5S 1G5,T5L 1B5,T5L 4L6,T5L 4H5,T5S 1Y6,T5S 0C1,T5S 2G2,T5L 0T6,T5M 3V9,T5S 2T9,T5V 0A4,T5M 3Z3,T5M 2S1,T5M 3N2,T5S 2J9,T5S 2P7,T5M 1V9,T5S 2W6,T5L 0A3,T5L 4R4,T5M 3N4,T5S 2J4,T5L 2Y7,T5M 3V3,T5S 2P3,T5S 2K8,T5V 1K8,T5S 1R2,T5L 4K8,T5L 4V5,T5S 1G9,T5L 2J5,T5V 1N9,T5V 1J8,T5M 1X7,T5S 1N3,T5S 1J6,T5M 2V6,T5V 1A7,T5M 3T9,T5S 2N4,T5L 2H6,T5S 2E1,T5L  4Y4,T5S 1Z7,T5S 2S8,T5L 0X3,T5S 1G6,T5L 0T3,T5M 2T8,T5S 1H2,T5V 1B6,T5L 2G7,T5L 0X6,T5S 2N6,T5S 2G5,T5S 0J1,T5V 0A2,T5V 1S9,T5V 0C3,T5S 1X6,T5L 4S8,T5L 4N7,T5V 0C1,T5S 0A4,T5S 1M7,T5V 1A4,T5M 4G4,T5V 1S5,T5S 2B5,T5V 1J9,T5L 3C8,T5M 1V3,T5S 1Y5,T5S 2W8,T5S 2C4,T5L 0N5,T5M 0H2,T5S 2L9,T5S 2H4,T5L 3E8,T5S 1G8,T5M 3Y2,T5M 4C8,T5S 2J7,T5V 1E6,T5S 2S9,T5V 1H3,T5M 1W5,T5L 2P1,T5L 2J2,T5L 4W7,T5M 1W7,T5V 1H5,T5S 0B2,T5V 1S8,T5M 0K8,T5S 1J8,T5M 2V7,T5S 1W9,T5L 0T5,T5S 2A9,T5S 1A1,T5S 1W6,T5L 4H7,T5S 1N6,T5M 3V1,T5L 4M9,T5M 0J1,T5L 0N6,T5V 1G9,T5M 2Y8,T5S 1H4,T5S 0G5,T5S 2L8,t5m 1l6,T5L 2L5,t5l 3b3,t5m 2z3,T5L 4L7,T5S 2E6,T5S 1L8,T5M 1Y2,T5L 2K6,T5S2T7,T5M 2H2,T5M 1Z9,T5M 3A6,T5L 5A3,T5M 2R1,T5L 5H5,T5L 2H9,T5L 2T3,t5l h3,T5M 3L5,T5S 2N5,T5M 4G6,T5S 1M2,T5M 4C7,T5S 1H6,T5S 2V3,T5S 1J9,T5S 2T7,T5m 2Z5,T5M 3R3,T5M 1V6,T5S 2V7,T5S 1C3,T5S 1N1,T5S 1G1,T5S 1X4,T5S 2W8,T5S 1K1,T5S 1C6,T5S 2M2,T5S 1L2,T5S 1P5,T5S 1S2,T5S 1M9,T5L 1C1,T5P 3Z5,T5L 0P1,T5P 2W9,T5P 0T6,T5P 3H9,T5P 1G8,T5S 0E5,T5S 2X8,T5P 1G9,T5M 3E9,t5v 1g6,T5S 2R5,T5P 3Z7,T5S 2S2,T5T 4J5,T5P 0H8,T5P 4C3,T5P 2P9,T5M 3Z5,T5L 3E5,T5P 1C3,T5S 2P2,T5S 1E7,T5S 2G9,T5P 4V6,T5L 0n9,T5L 4R6,T5L 2M5,t5v 1h1,T5M 3Y1,T5V 1V2,T5P 4P6,T5V 1R1,T5L 3L5,T5P 3S7,T5S 2E7,T5S 2T4,T5M 2Y9,T5P 2V5,T5L 1Y1,T5P 0Y1,T5P 3V4,T5M 4C6,T5P 0R2,T5S 1A8,T5N 2P5,T5S 0K3,T5V 1J4,T9E 1B7,T5P 4Y7,T5J 1J3,T5V 1A6,T5V 1S2,T5P 4K8,T5L 2W3,T5P 4Y1,T5M2S2,T5V 1H1,T5V 1M1,T5S 1N8,T5P 4P4,T6M 0L3,T5s 2m2,T5S 1E2,T5S 1J2,T5V 1M8,t5v 1s1,t5m2w1,T5S 1P7,T5V 0A2,T5S 0C6,T5L 0Y1,T5S 2L5,T5S 2K1,T5S 0A9,T5S 2J6,T5P 2G3,T5L 4R5,T5M 1Z1,T5P 3Z4,T5P 4B3,T5M 3W1,T5M 3S5,V4A 7G9,T5P 4W2,T5S 1N5,T5S 1T1,T5V 1M6,T5S 0C2,T5M 4G2,T5M 2X2,T5M 3Y3,T5S 1N9,T5P 0Y8,T5M 0J3,T5V 0B4,t5v 0b4,T5P 3W8,T5L 0X4,T5P 2W4,T5V 1A3,T5M 4B1,T5P 4V4,T5S 1R3,T5L 5H1,T5S 0C7,T5V 1L3,T5M 3R5,T5H 2Z9,T5M 1Y3,T5P 3Z6,T5L 3E1,T5S 2J4,T5P 3Z2,T5S 0C1,T5P 1C2,T5M 2L7,T6X 0Y8,T5P 3Y2,T5V 1H6,T5S 0B7,T5S 0A7,T5S 2X6,T5L 5B5,T5L 0J3,T5V 1H7,T5S 2E8,T5M 4G3,T5S 1V1,T5P 4M9,T5L 5G8,T5P 4B6,T5L 4W6,T5V 0C7,T5S 2S6,T5S 1K7,T5L 1A5,T5P 4W2,T5P 3Z1,T5S2H6,T5P 4V8,T5S 1A7,T5P 4H7,T6V,T5L 0H9,T5s 1S1,T5V 1m8,T5M 1V1,T5S 2L9,T5P 3X6,T5M 0T9,T5M 4C7,T5P 1G8,T5T 3X6,T5L 4X5,T5S 1J2,T5S 2K2,T5V 1B3,T5S 2L2,T5S 0C4,T5S 2X2,T5S 2V5,T5N,t5l 3c4,T6L 3L3,T5P 4M9,T5L-4L2,T5J 3M6,T5L4S8,T5L2M7,T5N 2L4,T5H 3P4,T5S 1C9,T5P 3C3,T5X 6C6,T5H 2Z8,T5V 1A2,T5S 2J2,T5V 1C3,T5L 2R8",
                },
                "ID": "d06d01d5-f153-4970-817b-dc8a6918d830",
                "ContactName": ".",
                "CompanyName": "(A) Bobcat of Edmonton",
                "AddressLine1": "14566 Yellowhead Trail",
                "AddressLine2": "",
                "City": "Edmonton",
                "State": "AB",
                "PostalCode": "T5L 3C5",
                "Country": "CA",
                "Comments": "",
                "Email": "",
                "Phone": "",
                "Category": "(A)",
                "LatitudeLongitude": "53.5818839,-113.5723291",
            },
            "DeliveryLocation": {
                "Zone": {
                    "ID": "5ee82c55-4c6e-48b6-9814-3c66f8d4a7b9",
                    "Name": "LEDUC/NISKU",
                    "PostalCodes": "T9E,T9E 0K2,T9E 0G9,T7A 1R4,T9E 8S6,T9E 8M1,T9E 8M3,T9E 8T3,T9E 8T2,T9E 0V3,T9E 0B5,T9E 7H3,T9E 0G8,T9E 7H7,T9E 8L7,T9E 7T8,T9E 7M3,T9E 5P5,T9E 8A8,T9E 6T6,T9E 0V4,T9E 7B2,T9E 6T8,T9E 0G4,T9E 8K2,T9E 0H2,T9E 7L1,T9E 7S7,T9E 7A9,T9E 7S4,T9E 8T4,T9E 6K2,T9E 7E6,T9E 7X2,T9E 7R1,T9E 7P8,T9E 0R8,T9E 7C3,T9E 7Y3,T9E 8B7,T9E 3C3,T9E 7E2,T9E 7Z2,T9E 7R5,T9E 7C9,T9E 0V7,T9E 7G3,T9E 7W5,T9E 0B3,T9E 7S5,T9E 2X2,T9E 7M5,T9E 8M4,T9E 7C6,T9E 1E6,T9E 7L2,T9E 7M1,T9E 7M7,T9E 6X1,T9E 7P4,T9E 5N5,T9E 8A7,T9E 7T1,T9E 0R6,T9E 8N4,T9E 7A8,T9E 8J4,T9E 6T2,T9E 8J1,T9E 7B9,T9E 7S8,T9E 1B7,T9E 7G1,T9E 7M9,T9E 8N5,T9E 7B4,T9E 7X7,T9E 7M8,T9E 8J8,T9E 6J4,T9E 7Y9,T9E 7A6,T9E 8B6,T9E 0H1,T9E 7B3,T9E 0K3,T9E 7E8,T9E 8H9,T9E 8M7,T9E 6Z6,T9E 8M8,T9E 0C2,T9E 7G4,T9E 6K8,T9E 0G5,T9E 0V6,T9E 7A4,T9E 8G7,T9E 8A1,T9E 7E5,T9E 8A5,T9E 7W1,T9E 7X3,T9E 7S6,T9E 0B7,T9E 7H8,T9E 7B1,T9E 7P1,T9E 7X5,T9E 7X8,T9E 7P9,T9E 7E4,T9E 7W9,T9E 8L1,T9E 0N1,T9E 8G6,T9E 7Z3,T9E 7Z7,T9E 7B8,T9E 8L6,T9E 8H4,T9E 7X4,T9E 0W1,T9E 7C2,T9E 0A9,T9E 7Y4,T9E 7A1,T9E 6X8,T9E 7A9,T9E 7T8,T9E 0R6,T9E 7K9,T9E 6Y9,T9E 6Z7,T9E 2X3,T9E 6Y6,T9E 6K6,T9E 5Z3,T9E 6S7,T9E 6Z9,T9E 7T7,T9E 0Z4,T9E 7T5,T9E 6Y8,T9E 7H5,T9E 7Z1,T9E 7M4,T9E 7V8,T9E 7L5,T9E 0K6,T9E 7X9,T9E 7W4,T9E 7A3,T9E 8G3,T9E 7E3,T9E 0K5,T9E 8J2,T9E 7Y8,T9E 7Y5,T9E 8M5,T9E 8M6,T9E 7G2,T9E 6T7,T9E 0B6,T9E 7R9,T9E 7B6,T9E 7R3,T9E 7S2,T9E 7X6,T9E 7V7,T9E 7P2,T9E 6M3,T9E 0G6,T9E 0L1,T9E 8H6,T9E 0K4,T9E 0B2,T9E 5S1,T9E 8P8,T9E 7A5,T9E 7C7,T9E 4X4,T9E 8G2,T9E 7N5,T9E 6T3,T9E 7N8,T9E 8K3,T9E 7R7,T9E 7Y2,T9E 7E1,T9E 7P7,T9E 3Z1,T9E 0A5,T9E 5W3,T9E 0L2,T9E 0B9,T9E 6T9,T9E 6X2,T9E 6V9,T9E 8A2,T9E 0A7,T9E 0V4,T9E 0N7,T9E 0Z3,T9E 4X5,T9E 0B6,T9E 7P3,T9E 7N7,T9E 7Z4,T9E 7R6,T9E 6Y3,T9E 8J7,T9E 1B3,T9E 7E7,T9E 2W9,T9G 1A8,T9E 7W3,T9E 5V8,T6E 0A5,T0C 2K0,T9E 8H7,T9E 0H3,T9E 8H,T9E 0C3,T9E 8M2,T9E 0M7,T9E 7N3,T0C 0V0,T9E 0C1,T9E 0A8,T9E 7R8,T9E 8H8,T9E 4C4,T9E 7L9,T9E 7P6,T9E 7B7,T5L 4T4,t9e 7c9,T9E 6Z1,T9E 7G9,T9E 8C7,T9E 0Y2,T9E 7W2,T9E 7S2,T9E 7V9,T9E 7T9,T9E 7V4,T9E 7X1,T9E 7C5,T9E 0A6,T9E 7N9,T9E 1C5,T9E 7E9,T9E 8J5,T9E 7M6,T9E 7Y7,T9E 6Z3,T9E 8G4,T9E 8A3,T9E 1C6,T9E 7Z3,T9G 0H7,T9E 7M9,T9E 7N5,T9E 7Z6,T9E 0G9,T9E 7J1,T9E7L6,T9E 0Z5,T9E 0Z4,T9E 8M4,T9E 7B9,T9E 0Y2,T9E 6Z8,T9E 8B8,T9E 0R8,T6W 1A7,T9E 1E7,T4X 0M1,T9E 7S6,T9E 8J7,T9E 1B3,t9e 7p2,T6X 1E9,T9E 0W8,t9c 1n6,T9G 1G2,t9a 3b6,t9e 7e2,T9G 2A9,t9e 7w8,T9E 0E6,T6B 3R7,T9E 6B7,T9E 0v4,t9e 7x4,T9E 7L6,T9E 0H5,T9E 0A3,T9G 1A6,T9E 8L9,T9E 0P3,T9E2X2,T9E 7E8,T9E 6T6,T9E 0G5,T9E 7N6,T6E 0E9,T9E 7S5,T6X 1Z9,T9E7C5,T9E 6V3,T5L 4H6,K8A 6W7,T6X 0C3,T6W,T6E 6J2,T5L 2M5,T9E 0M9,T9E 1E4,T0B 3M4,T9E 7W8,T9E 0S1,T9E 0W1,t6b 1z3,T7A 1E1,T9E 7A3,T9E 7Z1,T6B 1E7,T9E 0H1,T6B-0B4,T9E 7E8,T5L,T5W 0X8,T6E OV3,T6B,T5J 2T2,T6E,T9E 0K3,T9E 6P1,T9E 0S2,T0C 2G0,T9E 2A1,T9E 8S8,T9E 7R7,t9e 0z4,t9e 7s2,T6E 0R9,T5L 4N9,T9E 6W2,T6T 0B3,T9E 5J1,T9E 6N7,T9E 7B3,T9E 7B5,T9E 7A6,T9E 0N6,T9E 8A3,T9E 0v6,T6X,t9e 7v8,t9e 7z3,t6e 5t6,T6X 0E3,T9E 8A3,T6H 3H4,t6e 6w2,T6E 3L2,T9E 0S3,T9e 7B3,T9E 7V8,T9E 7A2,t9e 0r8,T9E 7M1,T9E 8T3,t9e 7ya,T9E 7W1,T9E 0M2,T9E 4L8,T6E 5R6,t9e 0a6,T9E 6W9,t9e 0c2,T6X 1G4,t9k 8k2,T9E 8R4,T9E 5V9,T5L 4S8,t9e 0b3,T9E 0A4,T9E 8L1,t9e 7y7,T6B OA3,t6e 0b8,T9K 8K2,T6E 7X6,T5L 2M7,T9W 8C7,T9E 6V6,T6W 3G9,T9E 0Z5,T9E 4C4,T9E 9S5,T9E 7W6,t9e 0r4,T9E 7Y5,t9e 7v8,T9E S75,t9e 0z4,T9e 8M1,T9E 7W7,T9E 0T1,t9e 7s8,T4X 0T4,T6T 1Y5,T9E 0V3,AB,T9E 7L3",
                },
                "ID": "348ea1bb-dedf-4095-a077-0dea4b51c8fe",
                "ContactName": "Bay 6",
                "CompanyName": "(A) BBE (reference numbers that start with FF)",
                "AddressLine1": "1759 35 Avenue East",
                "AddressLine2": "",
                "City": "Nisku",
                "State": "AB",
                "PostalCode": "T9E 0V6",
                "Country": "CA",
                "Comments": "",
                "Email": "",
                "Phone": "",
                "Category": "(A)",
                "LatitudeLongitude": "53.2926473,-113.5613812",
            },
            "Status": {
                "ID": "00000000-0000-0000-0000-000000000000",
                "Name": None,
                "Description": None,
                "Timestamp": "2021-09-07T22:02:07",
                "Level": 3,
            },
            "UserDefinedFields": {
                "Third Party Deliveries (Enter Customer to be Billed)": {
                    "Label": "Third Party Deliveries (Enter Customer to be Billed)",
                    "OrderID": "0b96f0c4-494c-42b5-bfb0-01851d5b80e1",
                    "ValueAsString": "",
                    "ValueAsDecimal": 0.0,
                    "ValueAsBoolean": False,
                    "ValueAsDate": "0001-01-01T00:00:00",
                },
                "Double Checked by Bill Specialist": {
                    "Label": "Double Checked by Bill Specialist",
                    "OrderID": "0b96f0c4-494c-42b5-bfb0-01851d5b80e1",
                    "ValueAsString": None,
                    "ValueAsDecimal": 0.0,
                    "ValueAsBoolean": True,
                    "ValueAsDate": "0001-01-01T00:00:00",
                },
                "CLICK HERE TO SEND ORDERS COLLECT *****NEW FEATURE*****": {
                    "Label": "CLICK HERE TO SEND ORDERS COLLECT *****NEW FEATURE*****",
                    "OrderID": "0b96f0c4-494c-42b5-bfb0-01851d5b80e1",
                    "ValueAsString": None,
                    "ValueAsDecimal": 0.0,
                    "ValueAsBoolean": False,
                    "ValueAsDate": "0001-01-01T00:00:00",
                },
            },
            "UserMiscCompensations": [],
            "VehicleRequired": {
                "ID": "dd027eda-e80b-45cd-b109-d839b8644645",
                "Name": "1.   3/4 Ton",
            },
            "PriceModifiers": [
                {
                    "ID": "827ac53b-3cae-40a2-a5ad-c714bb3884b3",
                    "Name": "BBE To & From Edmonton Area ",
                    "CustomValue": 0.0,
                    "PercentCommissionable": 100.0,
                    "Price": 10.0,
                    "Type": 0,
                    "Input": 0,
                }
            ],
            "TaxTotal": 0.0,
            "Subtotal": 10.0,
            "ID": "0b96f0c4-494c-42b5-bfb0-01851d5b80e1",
            "TrackingNumber": "1009214",
            "RequestedBy": "Ubbe",
            "BasePrice": 0.0,
            "CODAmount": 0.0,
            "BasePriceType": 2,
            "PriceAdjustment": 0.0,
            "PriceModifierTotalCost": 10.0,
            "Description": "1/Box\r\nOrigin\r\nBobcat Edmonton\r\nShipping\r\nexpediting@bbex.com\r\n7804484522\r\n14566 Yellowhead Trail\r\nEdmonton, AB T5L3C5\r\nDestination\r\nAcdc Co Bbe Expediting\r\nKim Douglas\r\nexpediting@bbex.con\r\n7808906893\r\n1759-35 avenue east\r\nEdmonton, AB T9E0V6\r\n",
            "Comments": "",
            "DateSubmitted": "2021-09-07T16:19:59",
            "RouteName": None,
            "StatusLevel": 3,
            "CollectionArrivalDate": "2021-09-07T17:11:37",
            "CollectionContactName": ".",
            "CollectionCODRequired": False,
            "CollectionSignatureRequired": False,
            "DeliveryArrivalDate": "2021-09-07T22:02:07",
            "DeliveryContactName": "Mohamed ",
            "DeliveryCODRequired": False,
            "DeliverySignatureRequired": False,
            "Distance": 38.3,
            "Height": 0.0,
            "Width": 0.0,
            "Length": 0.0,
            "Weight": 10.0,
            "Quantity": 1,
            "DeclaredValue": 0.0,
            "ReferenceNumber": "ub7606916492M",
            "PurchaseOrderNumber": "6707011766",
            "IncomingTrackingNumber": "",
            "OutgoingTrackingNumber": "",
            "TotalCost": 10.0,
            "SubmissionSource": "1",
        }

        self.ac_ship = ActionExpressShip(ubbe_request=self.request)

    def test_format_response(self) -> None:
        """
        Test Package item for rate formatting.
        """

        self.ac_ship._format_response(
            response=self.response,
            service_name="Double Rush",
            service_cost=Decimal("10.00"),
        )
        expected = {
            "carrier_id": 601,
            "carrier_name": "Action Express",
            "service_code": "REG",
            "service_name": "Double Rush",
            "freight": Decimal("0.00"),
            "surcharges": [],
            "surcharges_cost": Decimal("10.00"),
            "tax_percent": Decimal("5.00"),
            "taxes": Decimal("0.50"),
            "total": Decimal("10.50"),
            "tracking_number": "1009214",
            "pickup_id": "",
            "transit_days": 1,
            "delivery_date": "2021-09-09T00:00:00",
            "carrier_api_id": "0b96f0c4-494c-42b5-bfb0-01851d5b80e1",
        }
        self.assertEqual(expected, self.ac_ship._response)
