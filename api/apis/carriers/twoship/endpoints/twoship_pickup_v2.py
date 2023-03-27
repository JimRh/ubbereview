"""
    Title: 2Ship Pickup api
    Description: This file will contain functions related to 2Ship Pickup Api.
    Created: January 11, 2023
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from django.db import connection

from api.apis.carriers.twoship.endpoints.twoship_base_v2 import TwoShipBase
from api.exceptions.project import RequestError, ViewException, PickupException


class TwoShipPickup(TwoShipBase):
    """
    2Ship Ship Class
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)
        self._carrier_id = self._ubbe_request["carrier_id"]
        self._service_code = self._ubbe_request["service_code"]
        self._service_name = self._ubbe_request.get("service_name")

    def _get_package_totals(self) -> tuple:
        """
        Get Package totals for pickup requests.
        :return: Tuple contains Total Package and Total Weight
        """
        total_quantity = 0
        total_weight = Decimal("0.00")

        for package in self._ubbe_request["packages"]:
            quantity = package["quantity"]

            total_quantity += quantity
            total_weight += package["weight"] * Decimal(str(quantity))

        return total_quantity, total_weight

    def _build_request(self) -> dict:
        """
        Build 2Ship pickup request from ubbe request.
        :return: 2Ship Pickup Request
        """
        pickup = self._ubbe_request["pickup"]
        measurement_type = self._measurement_type_imperial
        service_type = (
            self._ground_service
            if "ground" in self._service_name.lower()
            else self._express_service
        )

        if self._ubbe_request["is_metric"]:
            measurement_type = self._measurement_type_metric

        total_quantity, total_weight = self._get_package_totals()

        ret = {
            "WS_Key": self._api_key,
            "LocationID": self._bbe_yeg_ff_location_id,
            "CarrierId": self._carrier_id,
            "PickupDate": pickup["date"].strftime("%Y-%m-%d"),
            "ReadyTime": pickup["start_time"],
            "CompanyCloseTime": pickup["end_time"],
            "PickupDescription": self._ubbe_request["special_instructions"],
            "PickupAddress": self._build_address(
                address=self._ubbe_request["origin"], carrier_id=self._carrier_id
            ),
            "ShipmentData": {
                "DestinationCountry": self._ubbe_request["destination"]["country"],
                "MeasurementsType": measurement_type,
                "ServiceType": service_type,
                "ServiceCode": self._service_code,
                "NumberOfPackage": total_quantity,
                "TotalWeight": total_weight,
            },
        }

        return ret

    def pickup(self) -> dict:
        """
        Create 2Ship Pickup request and return the pickup number.
        :return: Dict of Pickup information
        """

        if not self._service_name:
            connection.close()
            raise PickupException(
                "2Ship Ship (L361): 'service_name' must be in ubbe request."
            )

        try:
            request = self._build_request()
        except KeyError as e:
            connection.close()
            raise PickupException(f"2Ship Ship (L367): {str(e)}") from e

        try:
            response = self._post(url=self._pickup_url, request=request)
        except ViewException as e:
            connection.close()
            raise PickupException(f"2Ship Ship (L367): {e.message}") from e
        except RequestError as e:
            connection.close()
            raise PickupException(f"2Ship Ship (L367): {str(e)}") from e

        if response["IsError"]:
            return {
                "pickup_id": "",
                "pickup_message": response["ExceptionMessage"],
                "pickup_status": "Failed",
            }

        response = {
            "pickup_id": f'{response["PickupCarrierLocationCode"]}{response["PickupCarrierNumber"]}',
            "pickup_message": "Booked",
            "pickup_status": "Success",
        }

        return response

    def void(self) -> dict:
        """
        Void 2Ship Pickup.
        :return: Success Message
        """

        request = {
            "WS_Key": self._api_key,
            "CancelPickupRequestType": 1,
            "CarrierId": self._ubbe_request["carrier_id"],
            "PickupCarrierNumber": self._ubbe_request["pickup_id"],
        }

        try:
            response = self._post(url=self._cancel_pickup, request=request)
        except ViewException as e:
            connection.close()
            raise PickupException(f"2Ship Pickup (L367): {e.message}") from e
        except RequestError as e:
            connection.close()
            raise PickupException(f"2Ship Pickup (L367): {str(e)}") from e

        ret = {"is_canceled": True, "message": "Pickup Cancel."}

        return ret
