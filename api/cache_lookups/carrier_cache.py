"""
    Title: Carrier Cache Interface
    Description: This file will contain all functions for getting carrier information from cache.
    Created: July 14, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.core.cache import cache

from api.models import Carrier
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class CarrierCache:
    """
        Carrier Cache Interface
    """

    @staticmethod
    def _get_carrier_modes(mode: str) -> list:
        """
            Get list of carrier codes for a mode.
            :param mode: carrier mode code
            :return: carrier code list
        """

        return list(Carrier.objects.filter(mode__in=[mode]).values_list("code", flat=True))

    def get_carrier_list_mode(self, mode: str) -> list:
        """
            Get list of carrier codes for a mode, check cache then DB look it up and store.
            :param mode: carrier mode code
            :return: carrier code list
        """

        look_up = f"carrier_list_mode_{mode}"
        carriers = cache.get(look_up)

        if not carriers:
            carriers = self._get_carrier_modes(mode=mode)
            cache.set(look_up, carriers, TWENTY_FOUR_HOURS_CACHE_TTL)

        return carriers
