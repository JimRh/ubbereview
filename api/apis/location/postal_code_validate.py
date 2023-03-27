"""
    Title: Postal Code Validate
    Description: This file will contain all functions that will validate specific city names and postal codes.
    Created: Sept 14, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
import re

from api.apis.location.postal_validators.canada_validator import CanadaPostalCodeValidate
from api.exceptions.project import ViewException


class PostalCodeValidate:
    _CA = "CA"
    _US = "US"
    _ca_postal_format = re.compile("^([A-Z]\d){3}$")
    _us_postal_format = re.compile("^\d{5}$")

    def __init__(self, request: dict):
        self._request = copy.deepcopy(request)

        self._country = request["country"].upper()
        self._province = request["province"].upper()
        self._city = request["city"].lower()
        self._postal_code = request["postal_code"].replace(" ", "").upper()

    def _get_postal_code_format(self):
        """

            :return:
        """

        if self._country == self._CA:
            return self._ca_postal_format
        elif self._country == self._US:
            return self._us_postal_format

        return ""

    def validate(self) -> bool:
        """
            Validate Pickup request for carrier by using carrier specific restrictions or defaults.
            :return: Success message.
        """
        errors = []

        postal_format = self._get_postal_code_format()

        if postal_format:
            if not postal_format.match(self._postal_code):
                errors.append({"postal_code": "Please enter a valid postal/Zip Code."})

        if errors:
            raise ViewException(code="XXXXX", message="Postal Code Invalid.", errors=errors)

        if self._country == self._CA:
            CanadaPostalCodeValidate().validate(city=self._city, postal_code=self._postal_code, province=self._province)

        return True
