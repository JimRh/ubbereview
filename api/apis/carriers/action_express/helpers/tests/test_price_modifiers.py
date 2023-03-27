"""
    Title: Action Express Price Modifiers Unit Tests
    Description: Unit Tests for the Action Express Price Modifiers. Test Everything.
    Created: Sept 08, 2021
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""
import copy
import datetime
import re
from decimal import Decimal
from unittest.mock import patch

import pytz
from django.test import TestCase

from api.apis.carriers.action_express.helpers.price_modifiers import PriceModifier
from api.exceptions.project import RateException, RateExceptionNoEmail


class ACOrderTests(TestCase):
    def setUp(self):
        tz = pytz.timezone("America/Edmonton")
        self.date = datetime.datetime.now(tz)

        self.order = {
            "PriceSet": "a79c8ce0-f59d-4ed2-8fa9-0b114bd21970",
            "Customer": "bdd21daf-7078-4325-80df-0a95f90eb665",
            "CustomerContact": {
                "Name": "Customer Service",
                "Email": "customerservice@ubbe.ca",
                "Phone": "8884206926",
            },
            "Items": [
                {
                    "Description": "Package",
                    "Length": "20",
                    "Width": "20",
                    "Height": "20",
                    "Weight": "20",
                }
            ],
            "CollectionLocation": {
                "ContactName": "",
                "CompanyName": "BBE",
                "AddressLine1": "705-1st Avenue",
                "AddressLine2": "",
                "City": "Edmonton",
                "State": "AB",
                "PostalCode": "T5T4R7",
                "Country": "CA",
                "Email": "",
                "Phone": "",
            },
            "DeliveryLocation": {
                "ContactName": "",
                "CompanyName": "BBE",
                "AddressLine1": "705-1st Avenue",
                "AddressLine2": "",
                "City": "Edmonton International Airport",
                "State": "AB",
                "PostalCode": "T9E0V6",
                "Country": "CA",
                "Email": "",
                "Phone": "",
            },
            "CollectionArrivalWindow": {
                "EarliestTime": "2021-09-13T14:00:00+00:00",
                "LatestTime": "2021-09-14T00:00:00+00:00",
            },
            "RequestedBy": "BBE Expediting",
            "Description": "ubbe shipment",
            "CollectionSignatureRequired": True,
            "DeliverySignatureRequired": True,
            "ReferenceNumber": "/",
            "PurchaseOrderNumber": "",
            "Weight": 50.0,
            "Quantity": 2,
            "PriceModifiers": [],
        }

    def test_get_rush_option_none(self) -> None:
        """
        Test get rush option for rush.
        """

        ret, service, price = PriceModifier(order=self.order)._get_rush_option("10:00")
        expected = {}
        self.assertDictEqual(expected, ret)
        self.assertEqual("", service)
        self.assertEqual(Decimal(0.0), price)

    def test_get_rush_option_rush_one(self) -> None:
        """
        Test get rush option for rush.
        """

        ret, service, price = PriceModifier(order=self.order)._get_rush_option("12:00")
        expected = {
            "ID": "7285893c-2f1d-4ede-bb46-03c95c31ab27",
            "Name": "(1) Rush (Nisku)",
            "Price": 18.0,
        }
        self.assertDictEqual(expected, ret)
        self.assertEqual("RUSH:Rush", service)
        self.assertEqual(Decimal(18.0), price)

    def test_get_rush_option_rush_two(self) -> None:
        """
        Test get rush option for rush.
        """

        ret, service, price = PriceModifier(order=self.order)._get_rush_option("12:30")
        expected = {
            "ID": "7285893c-2f1d-4ede-bb46-03c95c31ab27",
            "Name": "(1) Rush (Nisku)",
            "Price": 18.0,
        }
        self.assertDictEqual(expected, ret)
        self.assertEqual("RUSH:Rush", service)
        self.assertEqual(Decimal(18.0), price)

    def test_get_rush_option_rush_three(self) -> None:
        """
        Test get rush option for rush.
        """

        ret, service, price = PriceModifier(order=self.order)._get_rush_option("13:29")
        expected = {
            "ID": "7285893c-2f1d-4ede-bb46-03c95c31ab27",
            "Name": "(1) Rush (Nisku)",
            "Price": 18.0,
        }
        self.assertDictEqual(expected, ret)
        self.assertEqual("RUSH:Rush", service)
        self.assertEqual(Decimal(18.0), price)

    def test_get_rush_option_double_rush_one(self) -> None:
        """
        Test get rush option for double rush.
        """

        ret, service, price = PriceModifier(order=self.order)._get_rush_option("13:30")
        expected = {
            "ID": "023e6428-04b5-41f6-b0db-1b10873af24b",
            "Name": "(2) Double Rush (Nisku)",
            "Price": 36.0,
        }
        self.assertDictEqual(expected, ret)
        self.assertEqual("DOUBLE:Double Rush", service)
        self.assertEqual(Decimal(36.0), price)

    def test_get_rush_option_double_rush_two(self) -> None:
        """
        Test get rush option for double rush.
        """

        ret, service, price = PriceModifier(order=self.order)._get_rush_option("14:00")
        expected = {
            "ID": "023e6428-04b5-41f6-b0db-1b10873af24b",
            "Name": "(2) Double Rush (Nisku)",
            "Price": 36.0,
        }
        self.assertDictEqual(expected, ret)
        self.assertEqual("DOUBLE:Double Rush", service)
        self.assertEqual(Decimal(36.0), price)

    def test_get_rush_option_double_rush_three(self) -> None:
        """
        Test get rush option for double rush.
        """

        ret, service, price = PriceModifier(order=self.order)._get_rush_option("14:29")
        expected = {
            "ID": "023e6428-04b5-41f6-b0db-1b10873af24b",
            "Name": "(2) Double Rush (Nisku)",
            "Price": 36.0,
        }
        self.assertDictEqual(expected, ret)
        self.assertEqual("DOUBLE:Double Rush", service)
        self.assertEqual(Decimal(36.0), price)

    def test_get_rush_option_direct_rush_one(self) -> None:
        """
        Test get rush option for direct rush.
        """

        ret, service, price = PriceModifier(order=self.order)._get_rush_option("14:30")
        expected = {
            "ID": "d7452d59-e971-4b8f-a02e-6d33e0e1068e",
            "Name": "(3) Direct Rush (Nisku)",
            "Price": 54.0,
        }
        self.assertDictEqual(expected, ret)
        self.assertEqual("DIRECT:Direct Rush", service)
        self.assertEqual(Decimal(54.0), price)

    def test_get_rush_option_direct_rush_two(self) -> None:
        """
        Test get rush option for direct rush.
        """

        ret, service, price = PriceModifier(order=self.order)._get_rush_option("15:00")
        expected = {
            "ID": "d7452d59-e971-4b8f-a02e-6d33e0e1068e",
            "Name": "(3) Direct Rush (Nisku)",
            "Price": 54.0,
        }
        self.assertDictEqual(expected, ret)
        self.assertEqual("DIRECT:Direct Rush", service)
        self.assertEqual(Decimal(54.0), price)

    def test_get_rush_option_direct_rush_three(self) -> None:
        """
        Test get rush option for direct rush.
        """

        ret, service, price = PriceModifier(order=self.order)._get_rush_option("16:00")
        expected = {
            "ID": "d7452d59-e971-4b8f-a02e-6d33e0e1068e",
            "Name": "(3) Direct Rush (Nisku)",
            "Price": 54.0,
        }
        self.assertDictEqual(expected, ret)
        self.assertEqual("DIRECT:Direct Rush", service)
        self.assertEqual(Decimal(54.0), price)

    def test_get_rush_option_direct_rush_four(self) -> None:
        """
        Test get rush option for direct rush.
        """

        ret, service, price = PriceModifier(order=self.order)._get_rush_option("16:30")
        expected = {
            "ID": "d7452d59-e971-4b8f-a02e-6d33e0e1068e",
            "Name": "(3) Direct Rush (Nisku)",
            "Price": 54.0,
        }
        self.assertDictEqual(expected, ret)
        self.assertEqual("DIRECT:Direct Rush", service)
        self.assertEqual(Decimal(54.0), price)

    def test_get_rush_option_direct_rush_five(self) -> None:
        """
        Test get rush option for direct rush.
        """

        ret, service, price = PriceModifier(order=self.order)._get_rush_option("17:00")
        expected = {
            "ID": "d7452d59-e971-4b8f-a02e-6d33e0e1068e",
            "Name": "(3) Direct Rush (Nisku)",
            "Price": 54.0,
        }
        self.assertDictEqual(expected, ret)
        self.assertEqual("DIRECT:Direct Rush", service)
        self.assertEqual(Decimal(54.0), price)

    def test_get_rush_option_direct_rush_six(self) -> None:
        """
        Test get rush option for direct rush.
        """

        ret, service, price = PriceModifier(order=self.order)._get_rush_option("17:30")
        expected = {
            "ID": "d7452d59-e971-4b8f-a02e-6d33e0e1068e",
            "Name": "(3) Direct Rush (Nisku)",
            "Price": 54.0,
        }
        self.assertDictEqual(expected, ret)
        self.assertEqual("DIRECT:Direct Rush", service)
        self.assertEqual(Decimal(54.0), price)

    def test_get_price_modifier_bbe_to_from_edmonton_one(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="edmonton:edmontoninternationalairport"
        )
        expected = {
            "ID": "827ac53b-3cae-40a2-a5ad-c714bb3884b3",
            "Name": "BBE To & From Edmonton Area",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_edmonton_two(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="edmontoninternationalairport:edmonton"
        )
        expected = {
            "ID": "827ac53b-3cae-40a2-a5ad-c714bb3884b3",
            "Name": "BBE To & From Edmonton Area",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_nisku_leduc_one(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="edmonton:edmonton"
        )
        expected = {
            "ID": "5df4304d-e403-445f-9db4-42e1160b6b0b",
            "Name": "BBE To & From Nisku / Leduc",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_nisku_leduc_two(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="edmontoninternationalairport:leduc"
        )
        expected = {
            "ID": "5df4304d-e403-445f-9db4-42e1160b6b0b",
            "Name": "BBE To & From Nisku / Leduc",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_nisku_leduc_three(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="leduc:edmontoninternationalairport"
        )
        expected = {
            "ID": "5df4304d-e403-445f-9db4-42e1160b6b0b",
            "Name": "BBE To & From Nisku / Leduc",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_nisku_leduc_four(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(route="nisku:nisku")
        expected = {
            "ID": "5df4304d-e403-445f-9db4-42e1160b6b0b",
            "Name": "BBE To & From Nisku / Leduc",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_nisku_leduc_five(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(route="leduc:leduc")
        expected = {
            "ID": "5df4304d-e403-445f-9db4-42e1160b6b0b",
            "Name": "BBE To & From Nisku / Leduc",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_nisku_leduc_six(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(route="leduc:nisku")
        expected = {
            "ID": "5df4304d-e403-445f-9db4-42e1160b6b0b",
            "Name": "BBE To & From Nisku / Leduc",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_nisku_leduc_seven(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(route="nisku:leduc")
        expected = {
            "ID": "5df4304d-e403-445f-9db4-42e1160b6b0b",
            "Name": "BBE To & From Nisku / Leduc",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_nisku_leduc_eight(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="edmontoninternationalairport:nisku"
        )
        expected = {
            "ID": "5df4304d-e403-445f-9db4-42e1160b6b0b",
            "Name": "BBE To & From Nisku / Leduc",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_nisku_leduc_nine(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="nisku:edmontoninternationalairport"
        )
        expected = {
            "ID": "5df4304d-e403-445f-9db4-42e1160b6b0b",
            "Name": "BBE To & From Nisku / Leduc",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_one_one(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="edmontoninternationalairport:acheson"
        )
        expected = {
            "ID": "8f7d0753-767e-4205-9032-80b50bd2a269",
            "Name": "BBE To & From Surrounding Area #1",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_one_two(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="acheson:edmontoninternationalairport"
        )
        expected = {
            "ID": "8f7d0753-767e-4205-9032-80b50bd2a269",
            "Name": "BBE To & From Surrounding Area #1",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_one_three(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="edmontoninternationalairport:beaumont"
        )
        expected = {
            "ID": "8f7d0753-767e-4205-9032-80b50bd2a269",
            "Name": "BBE To & From Surrounding Area #1",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_one_four(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="beaumont:edmontoninternationalairport"
        )
        expected = {
            "ID": "8f7d0753-767e-4205-9032-80b50bd2a269",
            "Name": "BBE To & From Surrounding Area #1",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_one_five(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="edmontoninternationalairport:devon"
        )
        expected = {
            "ID": "8f7d0753-767e-4205-9032-80b50bd2a269",
            "Name": "BBE To & From Surrounding Area #1",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_one_six(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="devon:edmontoninternationalairport"
        )
        expected = {
            "ID": "8f7d0753-767e-4205-9032-80b50bd2a269",
            "Name": "BBE To & From Surrounding Area #1",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_one_seven(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="edmontoninternationalairport:sherwoodpark"
        )
        expected = {
            "ID": "8f7d0753-767e-4205-9032-80b50bd2a269",
            "Name": "BBE To & From Surrounding Area #1",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_one_eight(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="sherwoodpark:edmontoninternationalairport"
        )
        expected = {
            "ID": "8f7d0753-767e-4205-9032-80b50bd2a269",
            "Name": "BBE To & From Surrounding Area #1",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_one_nine(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="edmontoninternationalairport:stalbert"
        )
        expected = {
            "ID": "8f7d0753-767e-4205-9032-80b50bd2a269",
            "Name": "BBE To & From Surrounding Area #1",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_one_ten(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="stalbert:edmontoninternationalairport"
        )
        expected = {
            "ID": "8f7d0753-767e-4205-9032-80b50bd2a269",
            "Name": "BBE To & From Surrounding Area #1",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_one_eleven(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="edmontoninternationalairport:winterburn"
        )
        expected = {
            "ID": "8f7d0753-767e-4205-9032-80b50bd2a269",
            "Name": "BBE To & From Surrounding Area #1",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_one_twelve(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="winterburn:edmontoninternationalairport"
        )
        expected = {
            "ID": "8f7d0753-767e-4205-9032-80b50bd2a269",
            "Name": "BBE To & From Surrounding Area #1",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_two_one(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="edmontoninternationalairport:calmar"
        )
        expected = {
            "ID": "241d3d73-0b0a-4237-8c06-487d5ddbd2e5",
            "Name": "BBE To & From Surrounding Area #2",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_two_two(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="calmar:edmontoninternationalairport"
        )
        expected = {
            "ID": "241d3d73-0b0a-4237-8c06-487d5ddbd2e5",
            "Name": "BBE To & From Surrounding Area #2",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_two_three(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="edmontoninternationalairport:millet"
        )
        expected = {
            "ID": "241d3d73-0b0a-4237-8c06-487d5ddbd2e5",
            "Name": "BBE To & From Surrounding Area #2",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_two_four(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="millet:edmontoninternationalairport"
        )
        expected = {
            "ID": "241d3d73-0b0a-4237-8c06-487d5ddbd2e5",
            "Name": "BBE To & From Surrounding Area #2",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_two_five(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="edmontoninternationalairport:fortsaskatchewan"
        )
        expected = {
            "ID": "241d3d73-0b0a-4237-8c06-487d5ddbd2e5",
            "Name": "BBE To & From Surrounding Area #2",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_two_six(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="fortsaskatchewan:edmontoninternationalairport"
        )
        expected = {
            "ID": "241d3d73-0b0a-4237-8c06-487d5ddbd2e5",
            "Name": "BBE To & From Surrounding Area #2",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_two_nine(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="edmontoninternationalairport:enoch"
        )
        expected = {
            "ID": "241d3d73-0b0a-4237-8c06-487d5ddbd2e5",
            "Name": "BBE To & From Surrounding Area #2",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_two_ten(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="enoch:edmontoninternationalairport"
        )
        expected = {
            "ID": "241d3d73-0b0a-4237-8c06-487d5ddbd2e5",
            "Name": "BBE To & From Surrounding Area #2",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_two_eleven(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="edmontoninternationalairport:namao"
        )
        expected = {
            "ID": "241d3d73-0b0a-4237-8c06-487d5ddbd2e5",
            "Name": "BBE To & From Surrounding Area #2",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_two_twelve(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="namao:edmontoninternationalairport"
        )
        expected = {
            "ID": "241d3d73-0b0a-4237-8c06-487d5ddbd2e5",
            "Name": "BBE To & From Surrounding Area #2",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_two_thirteen(
        self,
    ) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="edmontoninternationalairport:oliver"
        )
        expected = {
            "ID": "241d3d73-0b0a-4237-8c06-487d5ddbd2e5",
            "Name": "BBE To & From Surrounding Area #2",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_two_fourteen(
        self,
    ) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="oliver:edmontoninternationalairport"
        )
        expected = {
            "ID": "241d3d73-0b0a-4237-8c06-487d5ddbd2e5",
            "Name": "BBE To & From Surrounding Area #2",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_two_fifteen(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="edmontoninternationalairport:sprucegrove"
        )
        expected = {
            "ID": "241d3d73-0b0a-4237-8c06-487d5ddbd2e5",
            "Name": "BBE To & From Surrounding Area #2",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_two_sixteen(self) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="sprucegrove:edmontoninternationalairport"
        )
        expected = {
            "ID": "241d3d73-0b0a-4237-8c06-487d5ddbd2e5",
            "Name": "BBE To & From Surrounding Area #2",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_two_seventeen(
        self,
    ) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="edmontoninternationalairport:stonyplain"
        )
        expected = {
            "ID": "241d3d73-0b0a-4237-8c06-487d5ddbd2e5",
            "Name": "BBE To & From Surrounding Area #2",
        }
        self.assertDictEqual(expected, ret)

    def test_get_price_modifier_bbe_to_from_surrounding_areas_two_eighteen(
        self,
    ) -> None:
        """
        Test get price modification.
        """

        ret = PriceModifier(order=self.order)._get_price_modifier(
            route="stonyplain:edmontoninternationalairport"
        )
        expected = {
            "ID": "241d3d73-0b0a-4237-8c06-487d5ddbd2e5",
            "Name": "BBE To & From Surrounding Area #2",
        }
        self.assertDictEqual(expected, ret)

    def test_get_america_edmonton_time(self) -> None:
        """
        Test current time.
        """

        ret = PriceModifier(order=self.order)._get_america_edmonton_time()
        pattern = re.compile("^([01]?[0-9]|2[0-3]):[0-5][0-9]$")

        self.assertIsInstance(ret, str)
        self.assertTrue(pattern.match(ret))

    @staticmethod
    def mock_normal_call():
        return "11:00"

    @staticmethod
    def mock_rush_call():
        return "12:00"

    @staticmethod
    def mock_double_rush_call():
        return "14:00"

    @staticmethod
    def mock_direct_rush_call():
        return "14:45"

    @patch(
        "api.apis.carriers.action_express.helpers.price_modifiers.PriceModifier._get_america_edmonton_time",
        new=mock_normal_call,
    )
    def test_add_rate_modifiers_normal(self) -> None:
        """
        Test adding correct rate modifiers.
        """

        ret = PriceModifier(order=self.order).add_rate_modifiers()
        expected = [
            (
                {
                    "PriceSet": "a79c8ce0-f59d-4ed2-8fa9-0b114bd21970",
                    "Customer": "bdd21daf-7078-4325-80df-0a95f90eb665",
                    "CustomerContact": {
                        "Name": "Customer Service",
                        "Email": "customerservice@ubbe.ca",
                        "Phone": "8884206926",
                    },
                    "Items": [
                        {
                            "Description": "Package",
                            "Length": "20",
                            "Width": "20",
                            "Height": "20",
                            "Weight": "20",
                        }
                    ],
                    "CollectionLocation": {
                        "ContactName": "",
                        "CompanyName": "BBE",
                        "AddressLine1": "705-1st Avenue",
                        "AddressLine2": "",
                        "City": "Edmonton",
                        "State": "AB",
                        "PostalCode": "T5T4R7",
                        "Country": "CA",
                        "Email": "",
                        "Phone": "",
                    },
                    "DeliveryLocation": {
                        "ContactName": "",
                        "CompanyName": "BBE",
                        "AddressLine1": "705-1st Avenue",
                        "AddressLine2": "",
                        "City": "Edmonton International Airport",
                        "State": "AB",
                        "PostalCode": "T9E0V6",
                        "Country": "CA",
                        "Email": "",
                        "Phone": "",
                    },
                    "CollectionArrivalWindow": {
                        "EarliestTime": "2021-09-13T14:00:00+00:00",
                        "LatestTime": "2021-09-14T00:00:00+00:00",
                    },
                    "RequestedBy": "BBE Expediting",
                    "Description": "ubbe shipment",
                    "CollectionSignatureRequired": True,
                    "DeliverySignatureRequired": True,
                    "ReferenceNumber": "/",
                    "PurchaseOrderNumber": "",
                    "Weight": 50.0,
                    "Quantity": 2,
                    "PriceModifiers": [
                        {
                            "ID": "827ac53b-3cae-40a2-a5ad-c714bb3884b3",
                            "Name": "BBE To & From Edmonton Area",
                        }
                    ],
                },
                "REG:Regular",
                Decimal("0.00"),
            )
        ]

        self.assertIsInstance(ret, list)
        self.assertListEqual(expected, ret)

    @patch(
        "api.apis.carriers.action_express.helpers.price_modifiers.PriceModifier._get_america_edmonton_time",
        new=mock_rush_call,
    )
    def test_add_rate_modifiers_normal_and_rush(self) -> None:
        """
        Test adding correct rate modifiers.
        """

        ret = PriceModifier(order=self.order).add_rate_modifiers()
        expected = [
            (
                {
                    "PriceSet": "a79c8ce0-f59d-4ed2-8fa9-0b114bd21970",
                    "Customer": "bdd21daf-7078-4325-80df-0a95f90eb665",
                    "CustomerContact": {
                        "Name": "Customer Service",
                        "Email": "customerservice@ubbe.ca",
                        "Phone": "8884206926",
                    },
                    "Items": [
                        {
                            "Description": "Package",
                            "Length": "20",
                            "Width": "20",
                            "Height": "20",
                            "Weight": "20",
                        }
                    ],
                    "CollectionLocation": {
                        "ContactName": "",
                        "CompanyName": "BBE",
                        "AddressLine1": "705-1st Avenue",
                        "AddressLine2": "",
                        "City": "Edmonton",
                        "State": "AB",
                        "PostalCode": "T5T4R7",
                        "Country": "CA",
                        "Email": "",
                        "Phone": "",
                    },
                    "DeliveryLocation": {
                        "ContactName": "",
                        "CompanyName": "BBE",
                        "AddressLine1": "705-1st Avenue",
                        "AddressLine2": "",
                        "City": "Edmonton International Airport",
                        "State": "AB",
                        "PostalCode": "T9E0V6",
                        "Country": "CA",
                        "Email": "",
                        "Phone": "",
                    },
                    "CollectionArrivalWindow": {
                        "EarliestTime": "2021-09-13T14:00:00+00:00",
                        "LatestTime": "2021-09-14T00:00:00+00:00",
                    },
                    "RequestedBy": "BBE Expediting",
                    "Description": "ubbe shipment",
                    "CollectionSignatureRequired": True,
                    "DeliverySignatureRequired": True,
                    "ReferenceNumber": "/",
                    "PurchaseOrderNumber": "",
                    "Weight": 50.0,
                    "Quantity": 2,
                    "PriceModifiers": [
                        {
                            "ID": "827ac53b-3cae-40a2-a5ad-c714bb3884b3",
                            "Name": "BBE To & From Edmonton Area",
                        }
                    ],
                },
                "REG:Regular",
                Decimal("0.00"),
            ),
            (
                {
                    "PriceSet": "a79c8ce0-f59d-4ed2-8fa9-0b114bd21970",
                    "Customer": "bdd21daf-7078-4325-80df-0a95f90eb665",
                    "CustomerContact": {
                        "Name": "Customer Service",
                        "Email": "customerservice@ubbe.ca",
                        "Phone": "8884206926",
                    },
                    "Items": [
                        {
                            "Description": "Package",
                            "Length": "20",
                            "Width": "20",
                            "Height": "20",
                            "Weight": "20",
                        }
                    ],
                    "CollectionLocation": {
                        "ContactName": "",
                        "CompanyName": "BBE",
                        "AddressLine1": "705-1st Avenue",
                        "AddressLine2": "",
                        "City": "Edmonton",
                        "State": "AB",
                        "PostalCode": "T5T4R7",
                        "Country": "CA",
                        "Email": "",
                        "Phone": "",
                    },
                    "DeliveryLocation": {
                        "ContactName": "",
                        "CompanyName": "BBE",
                        "AddressLine1": "705-1st Avenue",
                        "AddressLine2": "",
                        "City": "Edmonton International Airport",
                        "State": "AB",
                        "PostalCode": "T9E0V6",
                        "Country": "CA",
                        "Email": "",
                        "Phone": "",
                    },
                    "CollectionArrivalWindow": {
                        "EarliestTime": "2021-09-13T14:00:00+00:00",
                        "LatestTime": "2021-09-14T00:00:00+00:00",
                    },
                    "RequestedBy": "BBE Expediting",
                    "Description": "ubbe shipment",
                    "CollectionSignatureRequired": True,
                    "DeliverySignatureRequired": True,
                    "ReferenceNumber": "/",
                    "PurchaseOrderNumber": "",
                    "Weight": 50.0,
                    "Quantity": 2,
                    "PriceModifiers": [
                        {
                            "ID": "827ac53b-3cae-40a2-a5ad-c714bb3884b3",
                            "Name": "BBE To & From Edmonton Area",
                        },
                        {
                            "ID": "7285893c-2f1d-4ede-bb46-03c95c31ab27",
                            "Name": "(1) Rush (Nisku)",
                            "Price": 18.0,
                        },
                    ],
                },
                "RUSH:Rush",
                Decimal("18"),
            ),
        ]
        self.assertIsInstance(ret, list)
        self.assertListEqual(expected, ret)

    @patch(
        "api.apis.carriers.action_express.helpers.price_modifiers.PriceModifier._get_america_edmonton_time",
        new=mock_double_rush_call,
    )
    def test_add_rate_modifiers_normal_and_double_rush(self) -> None:
        """
        Test adding correct rate modifiers.
        """

        ret = PriceModifier(order=self.order).add_rate_modifiers()
        expected = [
            (
                {
                    "PriceSet": "a79c8ce0-f59d-4ed2-8fa9-0b114bd21970",
                    "Customer": "bdd21daf-7078-4325-80df-0a95f90eb665",
                    "CustomerContact": {
                        "Name": "Customer Service",
                        "Email": "customerservice@ubbe.ca",
                        "Phone": "8884206926",
                    },
                    "Items": [
                        {
                            "Description": "Package",
                            "Length": "20",
                            "Width": "20",
                            "Height": "20",
                            "Weight": "20",
                        }
                    ],
                    "CollectionLocation": {
                        "ContactName": "",
                        "CompanyName": "BBE",
                        "AddressLine1": "705-1st Avenue",
                        "AddressLine2": "",
                        "City": "Edmonton",
                        "State": "AB",
                        "PostalCode": "T5T4R7",
                        "Country": "CA",
                        "Email": "",
                        "Phone": "",
                    },
                    "DeliveryLocation": {
                        "ContactName": "",
                        "CompanyName": "BBE",
                        "AddressLine1": "705-1st Avenue",
                        "AddressLine2": "",
                        "City": "Edmonton International Airport",
                        "State": "AB",
                        "PostalCode": "T9E0V6",
                        "Country": "CA",
                        "Email": "",
                        "Phone": "",
                    },
                    "CollectionArrivalWindow": {
                        "EarliestTime": "2021-09-13T14:00:00+00:00",
                        "LatestTime": "2021-09-14T00:00:00+00:00",
                    },
                    "RequestedBy": "BBE Expediting",
                    "Description": "ubbe shipment",
                    "CollectionSignatureRequired": True,
                    "DeliverySignatureRequired": True,
                    "ReferenceNumber": "/",
                    "PurchaseOrderNumber": "",
                    "Weight": 50.0,
                    "Quantity": 2,
                    "PriceModifiers": [
                        {
                            "ID": "827ac53b-3cae-40a2-a5ad-c714bb3884b3",
                            "Name": "BBE To & From Edmonton Area",
                        }
                    ],
                },
                "REG:Regular",
                Decimal("0.00"),
            ),
            (
                {
                    "PriceSet": "a79c8ce0-f59d-4ed2-8fa9-0b114bd21970",
                    "Customer": "bdd21daf-7078-4325-80df-0a95f90eb665",
                    "CustomerContact": {
                        "Name": "Customer Service",
                        "Email": "customerservice@ubbe.ca",
                        "Phone": "8884206926",
                    },
                    "Items": [
                        {
                            "Description": "Package",
                            "Length": "20",
                            "Width": "20",
                            "Height": "20",
                            "Weight": "20",
                        }
                    ],
                    "CollectionLocation": {
                        "ContactName": "",
                        "CompanyName": "BBE",
                        "AddressLine1": "705-1st Avenue",
                        "AddressLine2": "",
                        "City": "Edmonton",
                        "State": "AB",
                        "PostalCode": "T5T4R7",
                        "Country": "CA",
                        "Email": "",
                        "Phone": "",
                    },
                    "DeliveryLocation": {
                        "ContactName": "",
                        "CompanyName": "BBE",
                        "AddressLine1": "705-1st Avenue",
                        "AddressLine2": "",
                        "City": "Edmonton International Airport",
                        "State": "AB",
                        "PostalCode": "T9E0V6",
                        "Country": "CA",
                        "Email": "",
                        "Phone": "",
                    },
                    "CollectionArrivalWindow": {
                        "EarliestTime": "2021-09-13T14:00:00+00:00",
                        "LatestTime": "2021-09-14T00:00:00+00:00",
                    },
                    "RequestedBy": "BBE Expediting",
                    "Description": "ubbe shipment",
                    "CollectionSignatureRequired": True,
                    "DeliverySignatureRequired": True,
                    "ReferenceNumber": "/",
                    "PurchaseOrderNumber": "",
                    "Weight": 50.0,
                    "Quantity": 2,
                    "PriceModifiers": [
                        {
                            "ID": "827ac53b-3cae-40a2-a5ad-c714bb3884b3",
                            "Name": "BBE To & From Edmonton Area",
                        },
                        {
                            "ID": "023e6428-04b5-41f6-b0db-1b10873af24b",
                            "Name": "(2) Double Rush (Nisku)",
                            "Price": 36.0,
                        },
                    ],
                },
                "DOUBLE:Double Rush",
                Decimal("36"),
            ),
        ]

        self.assertIsInstance(ret, list)
        self.assertListEqual(expected, ret)

    @patch(
        "api.apis.carriers.action_express.helpers.price_modifiers.PriceModifier._get_america_edmonton_time",
        new=mock_direct_rush_call,
    )
    def test_add_rate_modifiers_normal_and_direct_rush(self) -> None:
        """
        Test adding correct rate modifiers.
        """

        ret = PriceModifier(order=self.order).add_rate_modifiers()
        expected = [
            (
                {
                    "PriceSet": "a79c8ce0-f59d-4ed2-8fa9-0b114bd21970",
                    "Customer": "bdd21daf-7078-4325-80df-0a95f90eb665",
                    "CustomerContact": {
                        "Name": "Customer Service",
                        "Email": "customerservice@ubbe.ca",
                        "Phone": "8884206926",
                    },
                    "Items": [
                        {
                            "Description": "Package",
                            "Length": "20",
                            "Width": "20",
                            "Height": "20",
                            "Weight": "20",
                        }
                    ],
                    "CollectionLocation": {
                        "ContactName": "",
                        "CompanyName": "BBE",
                        "AddressLine1": "705-1st Avenue",
                        "AddressLine2": "",
                        "City": "Edmonton",
                        "State": "AB",
                        "PostalCode": "T5T4R7",
                        "Country": "CA",
                        "Email": "",
                        "Phone": "",
                    },
                    "DeliveryLocation": {
                        "ContactName": "",
                        "CompanyName": "BBE",
                        "AddressLine1": "705-1st Avenue",
                        "AddressLine2": "",
                        "City": "Edmonton International Airport",
                        "State": "AB",
                        "PostalCode": "T9E0V6",
                        "Country": "CA",
                        "Email": "",
                        "Phone": "",
                    },
                    "CollectionArrivalWindow": {
                        "EarliestTime": "2021-09-13T14:00:00+00:00",
                        "LatestTime": "2021-09-14T00:00:00+00:00",
                    },
                    "RequestedBy": "BBE Expediting",
                    "Description": "ubbe shipment",
                    "CollectionSignatureRequired": True,
                    "DeliverySignatureRequired": True,
                    "ReferenceNumber": "/",
                    "PurchaseOrderNumber": "",
                    "Weight": 50.0,
                    "Quantity": 2,
                    "PriceModifiers": [
                        {
                            "ID": "827ac53b-3cae-40a2-a5ad-c714bb3884b3",
                            "Name": "BBE To & From Edmonton Area",
                        }
                    ],
                },
                "REG:Regular",
                Decimal("0.00"),
            ),
            (
                {
                    "PriceSet": "a79c8ce0-f59d-4ed2-8fa9-0b114bd21970",
                    "Customer": "bdd21daf-7078-4325-80df-0a95f90eb665",
                    "CustomerContact": {
                        "Name": "Customer Service",
                        "Email": "customerservice@ubbe.ca",
                        "Phone": "8884206926",
                    },
                    "Items": [
                        {
                            "Description": "Package",
                            "Length": "20",
                            "Width": "20",
                            "Height": "20",
                            "Weight": "20",
                        }
                    ],
                    "CollectionLocation": {
                        "ContactName": "",
                        "CompanyName": "BBE",
                        "AddressLine1": "705-1st Avenue",
                        "AddressLine2": "",
                        "City": "Edmonton",
                        "State": "AB",
                        "PostalCode": "T5T4R7",
                        "Country": "CA",
                        "Email": "",
                        "Phone": "",
                    },
                    "DeliveryLocation": {
                        "ContactName": "",
                        "CompanyName": "BBE",
                        "AddressLine1": "705-1st Avenue",
                        "AddressLine2": "",
                        "City": "Edmonton International Airport",
                        "State": "AB",
                        "PostalCode": "T9E0V6",
                        "Country": "CA",
                        "Email": "",
                        "Phone": "",
                    },
                    "CollectionArrivalWindow": {
                        "EarliestTime": "2021-09-13T14:00:00+00:00",
                        "LatestTime": "2021-09-14T00:00:00+00:00",
                    },
                    "RequestedBy": "BBE Expediting",
                    "Description": "ubbe shipment",
                    "CollectionSignatureRequired": True,
                    "DeliverySignatureRequired": True,
                    "ReferenceNumber": "/",
                    "PurchaseOrderNumber": "",
                    "Weight": 50.0,
                    "Quantity": 2,
                    "PriceModifiers": [
                        {
                            "ID": "827ac53b-3cae-40a2-a5ad-c714bb3884b3",
                            "Name": "BBE To & From Edmonton Area",
                        },
                        {
                            "ID": "d7452d59-e971-4b8f-a02e-6d33e0e1068e",
                            "Name": "(3) Direct Rush (Nisku)",
                            "Price": 54.0,
                        },
                    ],
                },
                "DIRECT:Direct Rush",
                Decimal("54"),
            ),
        ]

        self.assertIsInstance(ret, list)
        self.assertListEqual(expected, ret)

    def test_add_rate_modifiers_error_no_price(self) -> None:
        """
        Test adding correct rate modifiers.
        """
        copied = copy.deepcopy(self.order)
        copied["CollectionLocation"]["City"] = "NOTFOUND"

        with self.assertRaises(RateExceptionNoEmail) as context:
            ret = PriceModifier(order=copied).add_rate_modifiers()

        self.assertEqual(
            "AE PriceModifier (L206): No Price Found.", context.exception.message
        )
