"""
    Title: YRC Ship api
    Description: This file will contain functions related to YRC Ship Api.
    Created:  January 18, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import base64
import datetime
import math

from django.core.cache import cache
from django.db import connection
from lxml import etree
from zeep import helpers
from zeep.exceptions import Fault

from api.apis.carriers.yrc.endpoints.yrc_base import YRCBaseApi
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import ShipException, RequestError
from api.globals.carriers import YRC
from api.globals.project import (
    DOCUMENT_TYPE_BILL_OF_LADING,
    DOCUMENT_TYPE_SHIPPING_LABEL,
)
from api.models import CityNameAlias
from api.utilities.date_utility import DateUtility
from brain.settings import YRC_SOAP_BASE_URL


class YRCShip(YRCBaseApi):
    """
    YRC Fright Ship Class
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

        self.create_connection()
        self._service = self._client.create_service(
            "{http://my.yrc.com/national/WebServices/2009/01/31/YRCSecureBOL.wsdl}IYRCSecureBOLBinding",
            f"{YRC_SOAP_BASE_URL}/national/webservice/YRCSecureBOL",
        )

        self._response = {}

    @staticmethod
    def _build_bol_detail(pickup_date: str) -> dict:
        """
        Build YRC ship address dictionary for passed in address.
        :param pickup_date: Pickup date in str mm/dd/yyyy.
        :return: YRC Bol detail section
        """

        return {
            "pickupDate": pickup_date,
            "role": "TP",
            "autoSchedulePickup": False,
            "autoEmailBOL": False,
            "paymentTerms": "P",
            "originAddressSameAsShipper": True,
        }

    @staticmethod
    def _build_documents() -> dict:
        """
        Build YRC ship document configuration, Standard BOL with 4X6 Shipping labels.
        :return: YRC document section
        """

        return {
            "generateBolPDF": True,
            "bolDocumentType": "STD",
            "generateShippingLabelsPDF": True,
            "numberOfLabelsPerShipment": 1,
            "labelStartingPosition": 1,
            "labelFormat": "CONT_4X6",
            "generateProLabelsPDF": False,
        }

    @staticmethod
    def _build_third_party() -> dict:
        """
        Build YRC ship third party dictionary. Defaults to BBE.
        :return: YRC third party section
        """

        return {
            "companyName": "BBE Expediting",
            "phoneNumber": "780-890-6811",
            "address": "1759 35 Ave E",
            "city": "Edmonton Intl Airport",
            "state": "AB",
            "zip": "T9E0V6",
            "country": "CAN",
        }

    @staticmethod
    def _build_option_value(option_code: str):
        """
        Build YRC Option value dictionary for option code.
        :param option_code: YRC Option value
        :return:
        """
        return {"serviceOptionType": option_code, "serviceOptionPaymentTerms": "P"}

    def _build_address(self, address: dict) -> dict:
        """
        Build YRC ship address dictionary for passed in address.
        :param address: Address dictionary
        :return: YRC Address section
        """

        country = address["country"]

        if country == self._US:
            country = self._USA
        elif country == self._MX:
            country = self._MEX
        else:
            country = self._CAN

        city = CityNameAlias.check_alias(
            alias=address["city"].lower(),
            province_code=address["province"],
            country_code=address["country"],
            carrier_id=YRC,
        )

        if len(address["phone"]) > 10:
            phone = address["phone"][:10]
        else:
            phone = address["phone"]

        return {
            "companyName": address["company_name"],
            "contactName": address["name"],
            "phoneNumber": phone,
            "address": address["address"],
            "city": city,
            "state": address["province"],
            "zip": address["postal_code"].replace(" ", "").upper(),
            "country": country,
        }

    def _build_packages(self, packages: []) -> list:
        """
        Build YRC package dictionary for ship request
        :param packages: ubbe package list.
        :return: YRC list of commodities dictionary
        """
        package_list = []

        for package in packages:
            package_code = "SKD"

            if package["package_type"] in self.package_type_map:
                package_code = self.package_type_map[package["package_type"]]

            freight_class = self._freight_class_map[
                package.get("freight_class", "70.00")
            ]

            item = {
                "productDesc": self._remove_special_characters(
                    string_value=package["description"]
                ),
                "handlingUnitQuantity": package["quantity"],
                "handlingUnitType": package_code,
                "length": math.ceil(int(package["imperial_length"])),
                "width": math.ceil(int(package["imperial_width"])),
                "height": math.ceil(int(package["imperial_height"])),
                "totalWeight": math.ceil(
                    int(package["imperial_weight"]) * package["quantity"]
                ),
                "freightClass": freight_class,
                "isHazardous": package["is_dangerous_good"],
            }

            if package["is_dangerous_good"]:
                item.update(
                    {
                        "hazmatInfo": {
                            "technicalName": package["proper_shipping_name"],
                            "shipmentDescribedPer": "T",
                            "unnaNumber": f'UN{package["un_number"]}',
                            "hazmatClass": package["class_div"],
                            "packagingGroup": package["packing_group_str"],
                            "emergency24hrPhone": "(888) 226-8832",
                        }
                    }
                )

            package_list.append(item)

        return package_list

    def _build_options(self, options: list) -> list:
        """
        Build YRC ship option list with ubbe option codes.
        :return: YRC Rate optopns
        """
        option_list = []

        if not self._ubbe_request["origin"].get("has_shipping_bays", True):
            option_list.append(
                self._build_option_value(option_code=self._yrc_residential_pickup)
            )

        if not self._ubbe_request["destination"].get("has_shipping_bays", True):
            option_list.append(
                self._build_option_value(option_code=self._yrc_residential_delivery)
            )

        if not options:
            return option_list

        for option in options:
            if option == self._inside_pickup:
                option_list.append(
                    self._build_option_value(option_code=self._yrc_inside_pickup)
                )
            elif option == self._inside_delivery:
                option_list.append(
                    self._build_option_value(option_code=self._yrc_inside_delivery)
                )
            elif option == self._power_tailgate_pickup:
                option_list.append(
                    self._build_option_value(
                        option_code=self._yrc_power_tailgate_pickup
                    )
                )
            elif option == self._power_tailgate_delivery:
                option_list.append(
                    self._build_option_value(
                        option_code=self._yrc_power_tailgate_delivery
                    )
                )
            elif option == self._delivery_appointment:
                option_list.append(
                    self._build_option_value(option_code=self._yrc_delivery_appointment)
                )
            # elif option == self._heated_truck:
            #     option_list.append(self._build_option_value(option_code=self._yrc_protect_from_freezing))

        return option_list

    def _build_reference_numbers(self):
        """
        Build YRC Reference number format.
        :return: Dictionary of References
        """
        refs = [
            {"refNumber": self._ubbe_request["order_number"], "refNumberType": "PO"}
        ]

        if (
            "reference_one" in self._ubbe_request
            and self._ubbe_request["reference_one"] != ""
        ):
            refs.append(
                {
                    "refNumber": self._remove_special_characters(
                        string_value=self._ubbe_request["reference_one"]
                    ),
                    "refNumberType": "CO",
                }
            )

        if (
            "reference_two" in self._ubbe_request
            and self._ubbe_request["reference_two"] != ""
        ):
            refs.append(
                {
                    "refNumber": self._remove_special_characters(
                        string_value=self._ubbe_request["reference_two"]
                    ),
                    "refNumberType": "RN",
                }
            )

        return refs

    def _build_service(self, service_parts: list, pickup_date):
        """
        Build YRC ship service level section.
        :return:
        """

        ret = {
            "deliveryServiceOption": self._rate_to_ship_services[service_parts[0]],
            # "quoteIDNumber": service_parts[1],
        }

        if service_parts[0] in [self._tcsa_service, self._tcsp_service]:
            if service_parts[0] == self._tcsa_service:
                time_type = "NOON"
            else:
                time_type = "FIVE_PM"

            delivery_date = pickup_date + datetime.timedelta(days=7)
            delivery_date = DateUtility().new_next_business_day(
                country_code=self._ubbe_request["destination"]["country"],
                prov_code=self._ubbe_request["destination"]["province"],
                in_date=delivery_date,
            )

            ret.update(
                {
                    "GTCAdditionalInfo": {
                        "dueByDate": delivery_date.strftime("%m/%d/%Y"),
                        "dueByTime": time_type,
                        "GTCproactiveNotification": {
                            "isProActiveNotificationSelected": False,
                            "contactName": "Customer Service",
                            "contactPhone": "888-420-6926",
                        },
                    }
                }
            )

        return ret

    def _create_request(self) -> dict:
        """
        Build YRC ship request.
        :return: ship request
        """
        customs = {}

        service_parts = self._ubbe_request["service_code"].split("|")
        special = self._remove_special_characters(
            string_value=self._ubbe_request.get("special_instructions", "")[:237]
        )

        if "pickup" in self._ubbe_request and self._ubbe_request["is_pickup"]:
            pickup_date = self._ubbe_request["pickup"]["date"]
        else:
            pickup_date = datetime.datetime.today().date()

        if self._ubbe_request.get("is_international", False):
            customs = self._build_address(address=self._ubbe_request["broker"])

        submit_bol = {
            "bolDetail": self._build_bol_detail(pickup_date=pickup_date.strftime("%m/%d/%Y")),
            "shipper": self._build_address(address=self._ubbe_request["origin"]),
            "consignee": self._build_address(address=self._ubbe_request["destination"]),
            "thirdParty": self._build_third_party(),
            "customsBroker": customs,
            "commodityInformation": {"weightTypeIdentifier": "LB"},
            "commodityItem": self._build_packages(
                packages=self._ubbe_request["packages"]
            ),
            "referenceNumbers": self._build_reference_numbers(),
            "specialInstuctions": {
                "dockInstructions": f"QID: {service_parts[1]}, {special}"
            },
            "deliveryServiceOptions": self._build_service(service_parts=service_parts, pickup_date=pickup_date),
            "bolLabelPDF": self._build_documents(),
        }

        if self._ubbe_request.get("carrier_options", []):
            submit_bol["serviceOptions"] = self._build_options(
                options=self._ubbe_request.get("carrier_options", [])
            )

        if not customs:
            del submit_bol["customsBroker"]

        ret = {"UsernameToken": self._build_soap_auth(), "submitBOLRequest": submit_bol}

        return ret

    def _format_response(self, response: dict):
        """
        Format YRC ship response and get cached rate quote costs for ubbe response
        :param response: json of yrc response
        :return: ubbe response
        """
        documents = []
        service_parts = self._ubbe_request["service_code"].split("|")
        service_code = service_parts[0]
        quote_id = service_parts[1]

        cached_rate = cache.get(f"{YRC}-{quote_id}-{service_code}")

        if not cached_rate:
            raise ShipException("No Cached Rate")

        cache.delete_pattern(f"{YRC}-{quote_id}*")

        if "encodedBolPdf" in response:
            encoded = base64.b64encode(response["encodedBolPdf"])
            documents.append(
                {
                    "document": encoded.decode("ascii"),
                    "type": DOCUMENT_TYPE_BILL_OF_LADING,
                }
            )

        if "encodedShippingLabelsPdf" in response:
            encoded = base64.b64encode(response["encodedShippingLabelsPdf"])
            documents.append(
                {
                    "document": encoded.decode("ascii"),
                    "type": DOCUMENT_TYPE_SHIPPING_LABEL,
                }
            )

        self._response = {
            "carrier_id": YRC,
            "carrier_name": self._carrier_name,
            "service_code": service_code,
            "service_name": self._services[service_code],
            "freight": cached_rate["freight"],
            "surcharges": [],
            "surcharges_cost": cached_rate["surcharge"],
            "tax_percent": cached_rate["tax_percent"],
            "taxes": cached_rate["tax"],
            "total": cached_rate["total"],
            "tracking_number": response["proNumber"],
            "pickup_id": "",
            "transit_days": cached_rate["transit_days"],
            "delivery_date": cached_rate["delivery_date"],
            "carrier_api_id": quote_id,
            "documents": documents,
        }

    def _bol_post(self, request: dict) -> dict:
        """
        Ship YRC shipment.
        :param request:
        :return: YRC Ship Response in json
        """

        try:
            response = self._service.submitBOL(**request)
        except (Fault, ValueError) as e:
            # print(etree.tounicode(self._history.last_sent['envelope']))
            print(etree.tounicode(self._history.last_received["envelope"]))
            error = f"submitBOL Error: {str(e)}, Data: {etree.tounicode(self._history.last_received['envelope'])}"
            CeleryLogger().l_critical.delay(
                location="yrc_ship.py line: 359",
                message=str({"api.error.yrc.ship": f"Zeep Failure: {str(error)}"}),
            )
            return {}

        try:
            json_response = helpers.serialize_object(response, dict)
        except Exception as e:
            raise ShipException(f"YRC Ship (L348): {str(e)}") from e

        return json_response

    def ship(self) -> dict:
        """
        Ship YRC shipment.
        :return:
        """

        try:
            request = self._create_request()
        except KeyError as e:
            connection.close()
            raise ShipException(f"YRC Ship (L367): {str(e)}") from e

        try:
            response = self._bol_post(request=request)
        except RequestError as e:
            connection.close()
            raise ShipException(f"YRC Ship (L373): {str(e)}") from e

        if response.get("statusCode") == "E" or not response:
            raise ShipException(
                f'YRC Ship (L377): {str(response.get("statusMessages", ""))}\n{request}'
            )

        try:
            self._format_response(response=response)
        except ShipException as e:
            connection.close()
            raise ShipException(
                f"YRC Ship (L382): {str(e.message)}\n{response}\n{request}"
            ) from e
        except Exception as e:
            connection.close()
            raise ShipException(
                f"YRC Ship (L385): {str(e)}\n{response}\n{request}"
            ) from e

        connection.close()
        return self._response
