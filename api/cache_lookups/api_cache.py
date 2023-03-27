"""
    Title: API Cache Interface
    Description: This file will contain all functions for getting api information from cache.
    Created: July 14, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist

from api.models import API
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class APICache:
    """
        API Cache Interface
    """

    @staticmethod
    def _get_api(api_name: str) -> dict:
        """
            Get API Object and return dictionary of it.
            :param api_name: api name
            :return: API Information Dictionary
        """

        try:
            api = API.objects.get(name=api_name)
        except ObjectDoesNotExist:
            raise Exception("")

        return {
            "name": api.name,
            "is_active": api.active,
            "category": api.category
        }

    def get_api_cache(self, api_name: str) -> dict:
        """
            Get API Information to check if an api is active.
            :param api_name: api name
            :return: api information Dictionary
        """

        look_up = f"api_active_{api_name}"
        api = cache.get(look_up)

        if not api:
            api = self._get_api(api_name=api_name)
            cache.set(look_up, api, TWENTY_FOUR_HOURS_CACHE_TTL)

        return api
