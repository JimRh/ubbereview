"""
    Title: Get Carrier Service Information
    Description: This file will contain all functions for getting service information.
    Created: July 7, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist

from api.globals.carriers import TST
from api.models import CarrierService
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class CarrierServiceCache:
    """
        Get Carrier Service Information for Rating
    """

    @staticmethod
    def _get_service(carrier_id: int, service_code: str) -> dict:
        """
            Get Carrier Service Object and return dictionary of it.
            :param carrier_id: Carrier ID (int)
            :param service_code: Service Code (str)
            :return: Service Information Dictionary
        """

        try:
            service = CarrierService.objects.get(carrier__code=carrier_id, code=service_code)
        except ObjectDoesNotExist:
            return{
                "description": "No Service",
                "exceptions": "No Service",
                "service_days": "No Service"
            }

        return {
            "description": service.description,
            "exceptions": service.exceptions,
            "service_days": service.service_days
        }

    def get_service_information(self, carrier_id: int, service_code: str) -> dict:
        """
            Get Carrier Service Information for carrier and service level.
            :param carrier_id: Carrier ID (int)
            :param service_code: Service Code (str)
            :return: Service Information Dictionary
        """
        service_code = copy.deepcopy(service_code)

        if carrier_id == TST:
            service_code = service_code[:2]

        look_up = f"rate_carrier_service_{carrier_id}_{service_code}"
        service_info = cache.get(look_up)

        if not service_info:
            service_info = self._get_service(carrier_id=carrier_id, service_code=service_code)
            cache.set(look_up, service_info, TWENTY_FOUR_HOURS_CACHE_TTL)

        return service_info
