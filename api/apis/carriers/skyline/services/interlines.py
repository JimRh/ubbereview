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

from api.models import CNInterline
from brain.settings import FIVE_HOURS_CACHE_TTL


class GetInterlineID:
    """
    Handles the creation of Pickup and Delivery to be passed to Skyline
    """

    _default_transit = -1

    def __init__(self, origin: str, destination: str):
        self.origin = origin
        self.destination = destination

    def check_interline_lane(self) -> bool:
        """
        Check if the lane is an canadian north interline lane.
        :return: bool
        """
        return CNInterline.objects.filter(
            origin=self.origin, destination=self.destination
        ).exists()

    def get_interline_code(self):
        """
        Get interline code for lane for skyline rate or ship request if it exists.
        :return:
        """

        lookup = f"CNInterline-{self.origin}-{self.destination}"
        interline = cache.get(lookup)

        if not interline:
            # Get Interline and set cache
            try:
                interline = CNInterline.objects.get(
                    origin=self.origin, destination=self.destination
                )
            except ObjectDoesNotExist:
                return None

            cache.set(lookup, interline, FIVE_HOURS_CACHE_TTL)

        return interline.interline_id
