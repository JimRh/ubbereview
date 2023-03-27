"""
    Title: Canada Postal Code Validate Tests
    Description: This file will contain all functions for Carrier Pickup Serializer Tests.
    Created: Sept 15, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
import re

from django.test import TestCase

from api.apis.location.postal_code_validate import PostalCodeValidate
from api.exceptions.project import ViewException


class CanadaPostalCodeValidateTests(TestCase):

    def setUp(self):

        self.ca_postal_code_json = {
            "country": "CA",
            "province": "AB",
            "city": "Edmonton",
            "postal_code": "T9E0V6"
        }

        self.ca_postal_code_north_json = {
            "country": "CA",
            "province": "NT",
            "city": "Inuvik",
            "postal_code": "X0E0T0"
        }

        self.ca_postal_code_bad_json = {
            "country": "CA",
            "province": "NT",
            "city": "Inuvik",
            "postal_code": "X0E0Y0"
        }

        self.us_postal_code_json = {
            "country": "US",
            "province": "KT",
            "city": "Lexington",
            "postal_code": "40511"
        }

        self.none_postal_code_json = {
            "country": "UU",
            "province": "UU",
            "city": "UU",
            "postal_code": "UU"
        }

    def test_get_postal_code_form_ca_valid(self):
        """
            Test getting CA postal code regex
        """

        ret = PostalCodeValidate(request=self.ca_postal_code_json)._get_postal_code_format()

        self.assertEqual(ret, re.compile("^([A-Z]\d){3}$"))

    def test_get_postal_code_form_us_valid(self):
        """
            Test getting US postal code regex
        """

        ret = PostalCodeValidate(request=self.us_postal_code_json)._get_postal_code_format()

        self.assertEqual(ret, re.compile("^\d{5}$"))

    def test_get_postal_code_form_invalid(self):
        """
            Test getting not postal code regex
        """

        ret = PostalCodeValidate(request=self.none_postal_code_json)._get_postal_code_format()

        self.assertEqual(ret, "")

    def test_ca_valid(self):
        """
            Test postal code, city, province validation.
        """

        ret = PostalCodeValidate(request=self.ca_postal_code_json).validate()

        self.assertTrue(ret)

    def test_ca_valid_north(self):
        """
            Test postal code, city, province validation.
        """

        ret = PostalCodeValidate(request=self.ca_postal_code_north_json).validate()

        self.assertTrue(ret)

    def test_us_valid(self):
        """
            Test postal code, city, province validation.
        """

        ret = PostalCodeValidate(request=self.us_postal_code_json).validate()

        self.assertTrue(ret)

    def test_none_valid(self):
        """
            Test postal code, city, province validation.
        """

        ret = PostalCodeValidate(request=self.none_postal_code_json).validate()

        self.assertTrue(ret)

    def test_valid_invalid_nt(self):
        """
            Test validate method.
        """

        with self.assertRaises(ViewException) as e:

            ret = PostalCodeValidate(request=self.ca_postal_code_bad_json).validate()

        self.assertIsInstance(e.exception.message, str)
        self.assertEqual(e.exception.message, "CA Postal Code Invalid.")

    def test_ca_invalid_north(self):
        """
            Test validate method.
        """
        postal = copy.deepcopy(self.ca_postal_code_north_json)
        postal["postal_code"] = "11111"

        with self.assertRaises(ViewException) as e:

            ret = PostalCodeValidate(request=postal).validate()

        self.assertIsInstance(e.exception.message, str)
        self.assertEqual(e.exception.message, "Postal Code Invalid.")
