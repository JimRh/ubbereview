"""
    Title: Action Express Rate Api
    Description: This file will contain functions related to Action Express Rate Apis.
    Created: June 14, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db import connection

from api.apis.carriers.action_express.endpoints.ac_api import ActionExpressApi
from api.exceptions.project import RequestError, TrackException


class ActionExpressOrder(ActionExpressApi):
    """
    Action Express Rate Class
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request, is_track=True)

    def get_order(self, api_tracking_id: str, carrier_account) -> dict:
        """
        Track Action Express shipment.
        :param api_tracking_id: action express order_id.
        :return:
        """

        self._auth = {"Authorization": carrier_account.api_key.decrypt()}
        self._price_set = carrier_account.account_number.decrypt()
        self._customer_id = carrier_account.contract_number.decrypt()

        try:
            order = self._get(url=self._url + f"/orders/{api_tracking_id}")
        except RequestError as e:
            connection.close()
            raise TrackException(
                f"AE Order (L100): {str(e)}, Data: {str(api_tracking_id)}"
            ) from e

        connection.close()
        return order
