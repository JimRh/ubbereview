"""
    Title: Transit Time Service
    Description: This file will contain functions to get Transit Time for a service.
    Created: July 5, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist

from api.models import TransitTime
from brain.settings import FIVE_HOURS_CACHE_TTL


class Transit:
    """
    Handles the creation of Pickup and Delivery to be passed to Skyline
    """

    _default_transit = -1

    def __init__(
        self, origin: str, destination: str, service_id: int, service_code: str
    ):
        self.origin = origin
        self.destination = destination
        self.service_id = service_id
        self.service_code = service_code

    def get_transit_time(self) -> int:
        """
        Get Transit Time for origin destination combo for service.
        :return: Transit Time
        """

        try:
            transit = TransitTime.objects.get(
                origin=self.origin,
                destination=self.destination,
                rate_priority_id=self.service_id,
            )
        except ObjectDoesNotExist:
            try:
                transit = TransitTime.objects.get(
                    origin=self.destination,
                    destination=self.origin,
                    rate_priority_id=self.service_id,
                )
            except ObjectDoesNotExist:
                return self._default_transit

        return transit.transit_max

    def transit_time(self) -> list:
        """
        Get Transit for Canadian North Service.
        :return: List of Dicts
        """
        first_lookup = f"CN{self.origin}-{self.destination}{self.service_id}"
        transit = cache.get(first_lookup)

        if not transit:
            transit = cache.get(f"CN{self.destination}-{self.origin}{self.service_id}")

        if not transit:
            # Get Transit and set cache
            transit = self.get_transit_time()

            if transit != self._default_transit:
                cache.set(first_lookup, transit, FIVE_HOURS_CACHE_TTL)

        return transit
