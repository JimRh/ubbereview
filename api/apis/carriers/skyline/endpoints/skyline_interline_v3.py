"""
    Title: Skyline Interline Api
    Description: This file will contain functions to get interlines for skyline route.
    Created: July 5, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

import requests
from django.db import connection

from api.exceptions.project import RequestError, ViewException
from api.globals.project import DEFAULT_TIMEOUT_SECONDS
from api.models import SubAccount
from brain.settings import SKYLINE_BASE_URL


class SkylineInterline:
    _interline_url = SKYLINE_BASE_URL + "/Interline/GetInterlineRoutes"
    # _interline_url = "https://merged5t_api.skyres.ca:47443/Interline/GetInterlineRoutes"

    def __init__(self, api_key: str, sub_account: SubAccount):
        self._response = []
        self._api_key = api_key
        self._sub_account = sub_account

    @staticmethod
    def _format_response(response: list, origin: str, destination: str) -> list:
        """
        Format skyline response into a common ubbe dict of lists.
        :param response:
        :return:
        """
        lanes = []

        if not response:
            raise ViewException("Skyline: No Interline lane (L65).")

        for lane in response:
            lanes.append(
                {
                    "origin": origin,
                    "destination": destination,
                    "interline_id": lane["GroupId"],
                    "interline_carrier": lane["Legs"][1]["Carrier"]["Name"],
                }
            )

        return lanes

    def _post(self, data: dict):
        """
        Make Skyline call for interline details.
        :param data: request data
        :return:
        """

        try:
            response = requests.post(
                self._interline_url, json=data, timeout=DEFAULT_TIMEOUT_SECONDS
            )
        except requests.RequestException:
            connection.close()
            raise RequestError(None, data)

        if not response.ok:
            connection.close()
            raise RequestError(response, {"url": self._interline_url, "data": data})

        try:
            response = response.json()
        except ValueError:
            connection.close()
            raise RequestError(None, {"url": self._interline_url, "data": data})

        if response["errors"]:
            connection.close()
            raise RequestError(
                response, {"url": self._interline_url, "error": str(e), "data": data}
            )

        return response["data"]

    def get_interline(self, origin: str, destination: str) -> list:
        """
        Get Interline details for passed in origin and destination and return the interline carrier and id.
        :param origin: Origin Airport Code
        :param destination: Destination Airport Code
        :return: Interline details
        """

        request = {
            "API_Key": self._api_key,
            "UltimateOriginCode": origin,
            "UltimateDestinationCode": destination,
        }

        try:
            response = self._post(data=request)
        except RequestError as e:
            connection.close()
            raise ViewException(f"Skyline Interline (L81): {str(e)}")

        lanes = self._format_response(
            response=response, origin=origin, destination=destination
        )

        return lanes
