"""
    Title: Purolator Service
    Description: This file will contain functions related to Purolator Service Apis.
    Created: November 17, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from lxml import etree
from zeep.exceptions import Fault

from api.apis.carriers.purolator.courier.endpoints.purolator_base import (
    PurolatorBaseApi,
)
from api.background_tasks.logger import CeleryLogger
from brain.settings import PURO_BASE_URL


class PurolatorService(PurolatorBaseApi):
    """
    Purolator Service Class
    """

    _version = "2.0"

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

        self.create_connection(
            wsdl_path="ServiceAvailabilityService.wsdl", version=self._version
        )
        self._service = self._client.create_service(
            "{http://purolator.com/pws/service/v2}ServiceAvailabilityServiceEndpoint",
            f"{PURO_BASE_URL}/EWS/V2/ServiceAvailability/ServiceAvailabilityService.asmx",
        )

    @staticmethod
    def _short_address(address: dict):
        """
        Create Purolator Short Address dictionary.
        :param address: Address dict
        :return:
        """
        return {
            "City": address["city"],
            "Province": address["province"],
            "Country": address["country"],
            "PostalCode": address["postal_code"],
        }

    @staticmethod
    def _formant_validate(response: dict):
        """
        Parse the response to grab the address data for ubbe api response by grabing the first entry in the
        response.
        :param response: Purolator Validate City Postal Code Response
        :return:
        """

        try:
            suggested_addresses = response["body"]["SuggestedAddresses"][
                "SuggestedAddress"
            ]
            address = suggested_addresses[0]["Address"]
        except Exception as e:
            CeleryLogger().l_warning.delay(
                location="purolator_service.py line: 54",
                message=str(
                    {
                        "api.error.dr.rate": f"Unable to format Puro Validate City Postal Code. {str(e)}"
                    }
                ),
            )
            return {}

        return {
            "city": address["City"],
            "province": address["Province"],
            "country": address["Country"],
            "postal_code": address["PostalCode"],
        }

    def get_service_options(self):
        """
        The GetServiceOptions method returns all available Purolator services for the specified origin and
        destination addresses.
        :return:
        """

        try:
            response = self._service.GetServicesOptions(
                _soapheaders=[
                    self._build_request_context(
                        reference="GetServicesOptions", version=self._version
                    )
                ],
                BillingAccountNumber=self._account_number,
                SenderAddress=self._short_address(address=self._ubbe_request["origin"]),
                ReceiverAddress=self._short_address(
                    address=self._ubbe_request["destination"]
                ),
            )
        except (Fault, ValueError) as e:
            error = f"GetServicesOptions Error {str(e)} Data {etree.tounicode(self._history.last_received['envelope'])}"
            CeleryLogger().l_warning.delay(
                location="purolator_service.py line: 82",
                message=str({"api.purolator.service": f"Error: {error}"}),
            )
            return {}

        return response

    def get_service_rules(self):
        """
        The GetServiceRules method returns all available Purolator products and options, as well as all the
        rules associated with the products and options. This includes all product min/max weights and dimensions,
        min/max pieces, product inclusions and exclusions, as well as option inclusions and exclusions.
        :return: Purolator Response
        """

        try:
            response = self._service.GetServiceRules(
                _soapheaders=[
                    self._build_request_context(
                        reference="GetServiceRules", version=self._version
                    )
                ],
                BillingAccountNumber=self._account_number,
                SenderAddress=self._short_address(address=self._ubbe_request["origin"]),
                ReceiverAddress=self._short_address(
                    address=self._ubbe_request["destination"]
                ),
            )
        except (Fault, ValueError) as e:
            error = f"GetServiceRules: Error {str(e)}, Data: {etree.tounicode(self._history.last_received['envelope'])}"
            CeleryLogger().l_warning.delay(
                location="purolator_service.py line: 107",
                message=str({"api.purolator.service": f"Error: {error}"}),
            )

            return {}

        return response

    def validate_city_postal(self, address: dict):
        """
        The ValidateCityPostalCodeZip method validates that the city/province (state)/postal (zip) code entered
        is correct. Should the combination be incorrect, the response message will return suggested values,
        based on the information entered.
        :return:
        """

        try:
            response = self._service.ValidateCityPostalCodeZip(
                _soapheaders=[
                    self._build_request_context(
                        reference="ValidateCityPostalCodeZip", version=self._version
                    )
                ],
                Addresses=[{"ShortAddress": self._short_address(address=address)}],
            )
        except (Fault, ValueError) as e:
            puro_response = etree.tounicode(self._history.last_received["envelope"])
            error = f"ValidateCityPostalCodeZip: Error {str(e)}, Data: {puro_response}"
            CeleryLogger().l_warning.delay(
                location="purolator_service.py line: 131",
                message=str({"api.purolator.service": f"Error: {error}"}),
            )
            return {}

        return self._formant_validate(response=response)
