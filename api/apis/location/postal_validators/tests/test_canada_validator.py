"""
    Title: Canada Postal Code Validate Tests
    Description: This file will contain all functions for Canada Postal Code Validate Tests.
    Created: Sept 15, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.test import TestCase
from api.apis.location.postal_validators.canada_validator import CanadaPostalCodeValidate
from api.exceptions.project import ViewException


class CanadaPostalCodeValidateTests(TestCase):

    def test_ab_postal_code_valid(self):
        """
            Test valid postal code for alberta.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="T", province="AB")
        self.assertTrue(ret)

    def test_ab_postal_code_invalid(self):
        """
            Test invalid postal code for alberta.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="Q", province="AB")
        self.assertFalse(ret)

    def test_bc_postal_code_valid(self):
        """
            Test valid postal code for British Columbia.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="V", province="BC")
        self.assertTrue(ret)

    def test_bc_postal_code_invalid(self):
        """
            Test invalid postal code for British Columbia.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="Q", province="BC")
        self.assertFalse(ret)

    def test_mb_postal_code_valid(self):
        """
            Test valid postal code for Manitoba.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="R", province="MB")
        self.assertTrue(ret)

    def test_mb_postal_code_invalid(self):
        """
            Test invalid postal code for Manitoba.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="Q", province="MB")
        self.assertFalse(ret)

    def test_nb_postal_code_valid(self):
        """
            Test valid postal code for New Brunswick.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="E", province="NB")
        self.assertTrue(ret)

    def test_nb_postal_code_invalid(self):
        """
            Test invalid postal code for New Brunswick.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="Q", province="NB")
        self.assertFalse(ret)

    def test_nl_postal_code_valid(self):
        """
            Test valid postal code for Newfoundland and Labrador.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="A", province="NL")
        self.assertTrue(ret)

    def test_nl_postal_code_invalid(self):
        """
            Test invalid postal code for Newfoundland and Labrador.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="Q", province="NL")
        self.assertFalse(ret)

    def test_ns_postal_code_valid(self):
        """
            Test valid postal code for Nova Scotia.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="B", province="NS")
        self.assertTrue(ret)

    def test_ns_postal_code_invalid(self):
        """
            Test invalid postal code for Nova Scotia.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="Q", province="NS")
        self.assertFalse(ret)

    def test_nt_postal_code_valid(self):
        """
            Test valid postal code for Northwest Territories.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="X", province="NT")
        self.assertTrue(ret)

    def test_nt_postal_code_invalid(self):
        """
            Test invalid postal code for Northwest Territories.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="Q", province="NT")
        self.assertFalse(ret)

    def test_nu_postal_code_valid(self):
        """
            Test valid postal code for Ontario.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="X", province="NU")
        self.assertTrue(ret)

    def test_nu_postal_code_invalid(self):
        """
            Test invalid postal code for Ontario.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="Q", province="NU")
        self.assertFalse(ret)

    def test_on_postal_code_valid(self):
        """
            Test valid postal code for Ontario.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="P", province="ON")
        self.assertTrue(ret)

    def test_on_postal_code_invalid(self):
        """
            Test invalid postal code for Ontario.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="Q", province="ON")
        self.assertFalse(ret)

    def test_on_postal_code_valid_two(self):
        """
            Test valid postal code for Ontario.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="L", province="ON")
        self.assertTrue(ret)

    def test_on_postal_code_invalid_two(self):
        """
            Test invalid postal code for Ontario.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="Q", province="ON")
        self.assertFalse(ret)

    def test_on_postal_code_valid_three(self):
        """
            Test valid postal code for Ontario.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="N", province="ON")
        self.assertTrue(ret)

    def test_on_postal_code_invalid_three(self):
        """
            Test invalid postal code for Ontario.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="Q", province="ON")
        self.assertFalse(ret)

    def test_on_postal_code_valid_four(self):
        """
            Test valid postal code for Ontario.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="M", province="ON")
        self.assertTrue(ret)

    def test_on_postal_code_invalid_four(self):
        """
            Test invalid postal code for Ontario.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="Q", province="ON")
        self.assertFalse(ret)

    def test_on_postal_code_valid_five(self):
        """
            Test valid postal code for Ontario.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="K", province="ON")
        self.assertTrue(ret)

    def test_on_postal_code_invalid_five(self):
        """
            Test invalid postal code for Ontario.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="Q", province="ON")
        self.assertFalse(ret)

    def test_pe_postal_code_valid(self):
        """
            Test valid postal code for Prince Edward Island.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="C", province="PE")
        self.assertTrue(ret)

    def test_pe_postal_code_invalid(self):
        """
            Test invalid postal code for Prince Edward Island.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="Q", province="PE")
        self.assertFalse(ret)

    def test_qc_postal_code_valid(self):
        """
            Test valid postal code for Québec.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="J", province="QC")
        self.assertTrue(ret)

    def test_qc_postal_code_invalid(self):
        """
            Test invalid postal code for Québec.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="Q", province="QC")
        self.assertFalse(ret)

    def test_qc_postal_code_valid_two(self):
        """
            Test valid postal code for Québec.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="G", province="QC")
        self.assertTrue(ret)

    def test_qc_postal_code_invalid_two(self):
        """
            Test invalid postal code for Québec.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="Q", province="QC")
        self.assertFalse(ret)

    def test_qc_postal_code_valid_three(self):
        """
            Test valid postal code for Québec.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="H", province="QC")
        self.assertTrue(ret)

    def test_qc_postal_code_invalid_three(self):
        """
            Test invalid postal code for Québec.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="Q", province="QC")
        self.assertFalse(ret)

    def test_qc_postal_code_valid_four(self):
        """
            Test valid postal code for Québec.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="H", province="QC")
        self.assertTrue(ret)

    def test_qc_postal_code_invalid_four(self):
        """
            Test invalid postal code for Québec.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="Q", province="QC")
        self.assertFalse(ret)

    def test_qc_postal_code_valid_five(self):
        """
            Test valid postal code for Québec.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="K", province="QC")
        self.assertTrue(ret)

    def test_qc_postal_code_invalid_five(self):
        """
            Test invalid postal code for Québec.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="Q", province="QC")
        self.assertFalse(ret)

    def test_sk_postal_code_valid(self):
        """
            Test valid postal code for Saskatchewan.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="S", province="SK")
        self.assertTrue(ret)

    def test_sk_postal_code_invalid(self):
        """
            Test invalid postal code for Saskatchewan.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="Q", province="SK")
        self.assertFalse(ret)

    def test_yt_postal_code_valid(self):
        """
            Test valid postal code for Yukon.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="Y", province="YT")
        self.assertTrue(ret)

    def test_yt_postal_code_invalid(self):
        """
            Test invalid postal code for Yukon.
        """

        ret = CanadaPostalCodeValidate._check_postal(postal_letter="Q", province="YT")
        self.assertFalse(ret)

    def test_check_nt_community_postal_valid(self):
        """
            Test valid postal code for aklavik.
        """

        ret = CanadaPostalCodeValidate._check_nt_community_postal(postal_code="X0E0A0", city="aklavik")
        self.assertTrue(ret)

    def test_check_nt_community_postal_invalid(self):
        """
            Test valid postal code for aklavik.
        """

        ret = CanadaPostalCodeValidate._check_nt_community_postal(postal_code="X0E0Y0", city="aklavik")
        self.assertFalse(ret)

    def test_check_nt_community_postal_valid_two(self):
        """
            Test valid postal code for inuvik.
        """

        ret = CanadaPostalCodeValidate._check_nt_community_postal(postal_code="X0E0T0", city="inuvik")
        self.assertTrue(ret)

    def test_check_nt_community_postal_invalid_two(self):
        """
            Test valid postal code for inuvik.
        """

        ret = CanadaPostalCodeValidate._check_nt_community_postal(postal_code="X0E0Y0", city="inuvik")
        self.assertFalse(ret)

    def test_check_nt_community_postal_valid_three(self):
        """
            Test valid postal code for hay river.
        """

        ret = CanadaPostalCodeValidate._check_nt_community_postal(postal_code="X0E0R9", city="hay river")
        self.assertTrue(ret)

    def test_check_nt_community_postal_invalid_three(self):
        """
            Test valid postal code for hay river.
        """

        ret = CanadaPostalCodeValidate._check_nt_community_postal(postal_code="X0E0V0", city="hay river")
        self.assertFalse(ret)

    def test_check_nu_community_postal_valid(self):
        """
            Test valid postal code for arviat.
        """

        ret = CanadaPostalCodeValidate._check_nu_community_postal(postal_code="X0C0E0", city="arviat")
        self.assertTrue(ret)

    def test_check_nu_community_postal_invalid(self):
        """
            Test valid postal code for arviat.
        """

        ret = CanadaPostalCodeValidate._check_nu_community_postal(postal_code="X0E0Y0", city="arviat")
        self.assertFalse(ret)

    def test_check_nu_community_postal_valid_two(self):
        """
            Test valid postal code for hall beach.
        """

        ret = CanadaPostalCodeValidate._check_nu_community_postal(postal_code="X0A0K0", city="hall beach")
        self.assertTrue(ret)

    def test_check_nu_community_postal_invalid_two(self):
        """
            Test valid postal code for hall beach.
        """

        ret = CanadaPostalCodeValidate._check_nu_community_postal(postal_code="X0A0B0", city="hall beach")
        self.assertFalse(ret)

    def test_check_nu_community_postal_valid_three(self):
        """
            Test valid postal code for iqaluit.
        """

        ret = CanadaPostalCodeValidate._check_nu_community_postal(postal_code="X0A0H0", city="iqaluit")
        self.assertTrue(ret)

    def test_check_nu_community_postal_invalid_three(self):
        """
            Test valid postal code for iqaluit.
        """

        ret = CanadaPostalCodeValidate._check_nu_community_postal(postal_code="X0A0W0", city="iqaluit")
        self.assertFalse(ret)

    def test_validate_valid_nu(self):
        """
            Test validate method.
        """

        ret = CanadaPostalCodeValidate().validate(city="iqaluit", postal_code="X0A0H0", province="NU")

        self.assertTrue(ret)

    def test_validate_valid_nt(self):
        """
            Test validate method.
        """

        ret = CanadaPostalCodeValidate().validate(city="inuvik", postal_code="X0E0T0", province="NT")

        self.assertTrue(ret)

    def test_validate_invalid_nt(self):
        """
            Test validate method.
        """

        with self.assertRaises(ViewException) as e:

            ret = CanadaPostalCodeValidate().validate(city="inuvik", postal_code="T9E0V6", province="NT")

        self.assertIsInstance(e.exception.message, str)
        self.assertEqual(e.exception.message, "CA Postal Code Invalid.")

    def test_validate_invalid_nt_two(self):
        """
            Test validate method.
        """

        with self.assertRaises(ViewException) as e:

            ret = CanadaPostalCodeValidate().validate(city="Edmonton", postal_code="X0E0T0", province="NT")

        self.assertIsInstance(e.exception.message, str)
        self.assertEqual(e.exception.message, "CA Postal Code Invalid.")

    def test_validate_invalid_nu(self):
        """
            Test validate method.
        """

        with self.assertRaises(ViewException) as e:

            ret = CanadaPostalCodeValidate().validate(city="iqaluit", postal_code="T9E0V6", province="NU")

        self.assertIsInstance(e.exception.message, str)
        self.assertEqual(e.exception.message, "CA Postal Code Invalid.")

    def test_validate_invalid_nu_two(self):
        """
            Test validate method.
        """

        with self.assertRaises(ViewException) as e:

            ret = CanadaPostalCodeValidate().validate(city="Edmonton", postal_code="X0A0H0", province="NU")

        self.assertIsInstance(e.exception.message, str)
        self.assertEqual(e.exception.message, "CA Postal Code Invalid.")
