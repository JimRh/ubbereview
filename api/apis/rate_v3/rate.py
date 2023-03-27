"""
    Title: Main Rate Class
    Description: This file will get rates for all available and validated carriers.
    Created: July 14, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import gevent
from django.contrib.auth.models import User

from api.apis.multi_modal.ground_rate import GroundRate
from api.apis.multi_modal.mc_ground_rate import MultiCarrierGroundRate
from api.apis.multi_modal.mm_air_rate import MultiModalAirRate
from api.apis.multi_modal.mm_sealift_rate import MultiModalSealiftRate
from api.apis.rate_v3.join_rates_v2 import JoinRateV2
from api.background_tasks.logger import CeleryLogger
from api.background_tasks.rate_logging import CeleryRateLog
from api.exceptions.project import ViewException
from api.models import RateLog, SubAccount
from api.parse_requests.parse_rate_request import ParseRateRequest
from api.utilities.carriers import CarrierUtility


class RateV3:
    """
        Rate V3

        Response: dict
            - rate_id - Log ID
            - rates  - List of rates
            - pickup_rates - List of Lists of Pickup Rates
            - delivery_rates - List of Lists of Delivery Rates
            - carrier_service - Carrier Service Information

        Steps:
            - Step 1 - Create Rate Log
            - Step 2 - Parse Rate Request
            - Step 3 - Get Carrier Information
            - Step 4 - Thread Carrier Rates
            - Step 5 - Apply Markups
            - Step 6 - Get Carrier Service Information
            - Step 7 - Update Rate Log With Response
            - Step 8 - Return Response
    """

    def __init__(self, ubbe_request: dict, log_data: dict, sub_account: SubAccount, user: User):

        self._ubbe_request = ubbe_request
        self._log_data = log_data
        self._sub_account = sub_account
        self._user = user

    @staticmethod
    def _get_tread_rate(thread, rate_type: str):

        try:
            rates = thread.get()
        except ViewException as e:
            CeleryLogger().l_debug.delay(location="rate_apis.py line: 295", message=f"{rate_type}: {str(e.message)}")
            return None
        except Exception as e:
            CeleryLogger().l_debug.delay(location="rate_apis.py line: 295", message=f"{rate_type}: {str(e)}")
            return None

        return rates

    def _create_rate_log(self) -> RateLog:
        """

            :return:
        """

        rate_log = RateLog.create(param_dict={
            "sub_account": self._sub_account,
            "rate_data": self._log_data,
            "response_data": '{}',
            "is_no_rate": True
        })
        rate_log.save()

        return rate_log

    def _get_carrier_information(self):
        """

            :return:
        """

        # Get additional objects that are used in multiple places.
        carrier_accounts = CarrierUtility().get_carrier_accounts(
            sub_account=self._sub_account,
            carrier_list=self._ubbe_request["carrier_id"]
        )

        self._ubbe_request["objects"] = {
            "sub_account": self._sub_account,
            "user": self._user,
            "carrier_accounts": carrier_accounts,
            "air_list": CarrierUtility().get_air(),
            "ltl_list": CarrierUtility().get_ltl(),
            "ftl_list": CarrierUtility().get_ftl(),
            "courier_list": CarrierUtility().get_courier(),
            "sealift_list": CarrierUtility().get_sealift()
        }

    def _get_rates(self) -> dict:
        """
            Get Rates for parse ubbe request.
            :return: dictionary of rates
        """

        gevent_ground = gevent.Greenlet.spawn(GroundRate(gobox_request=self._ubbe_request).rate)
        gevent_air = gevent.Greenlet.spawn(MultiModalAirRate(gobox_request=self._ubbe_request).rate)
        gevent_sealift = gevent.Greenlet.spawn(MultiModalSealiftRate(gobox_request=self._ubbe_request).rate)
        gevent_interline = gevent.Greenlet.spawn(MultiCarrierGroundRate(gobox_request=self._ubbe_request).rate)

        gevent.joinall([gevent_air, gevent_ground, gevent_sealift])

        ground_rates = self._get_tread_rate(thread=gevent_ground, rate_type="Ground")
        air_rates = self._get_tread_rate(thread=gevent_air, rate_type="Air")
        sealift_rates = self._get_tread_rate(thread=gevent_sealift, rate_type="Sea")
        interline_rates = self._get_tread_rate(thread=gevent_interline, rate_type="Interline")

        all_rates = JoinRateV2(
            rates=[air_rates, sealift_rates, ground_rates],
            sub_account=self._sub_account,
            carrier_accounts=self._ubbe_request["objects"]["carrier_accounts"]
        ).join_rates()

        return all_rates

    def rate(self) -> dict:
        """

            :return:
        """

        rate_log = self._create_rate_log()

        # Clean/Process Rate Request
        ParseRateRequest(ubbe_request=self._ubbe_request, sub_account=self._sub_account).parse()

        if not self._ubbe_request["carrier_id"]:
            raise ViewException(code="502", message="No available carriers for request", errors=[])

        self._get_carrier_information()

        response = self._get_rates()

        CeleryRateLog.log_rate_response.delay(rate_log_id=rate_log.rate_log_id, rate_response=response)

        response["rate_id"] = rate_log.rate_log_id

        return response
