"""
    Title: Google Api Base Class
    Description: This file will contain common functions between the different google apis.
    Created: March 2, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import gevent
from django.core.exceptions import ObjectDoesNotExist

from api.apis.google.route_apis.distance_api import GoogleDistanceApi
from api.models import MiddleLocation


class FindMiddleLocation:
    _distance_api = GoogleDistanceApi()

    @staticmethod
    def _get_shortest_middle_location(middle_data: list) -> MiddleLocation:
        """

            :param middle_data:
            :return:
        """
        location = min(middle_data, key=lambda l: l["distance"])
        return location["middle"]

    @staticmethod
    def _get_distance(origin: dict, middle: MiddleLocation, destination: dict) -> dict:
        """

            :param origin:
            :param middle:
            :param destination:
            :return:
        """

        middle_dict = {
            "city": middle.address.city.lower(),
            "province": middle.address.province.code,
            "country": middle.address.province.country.code
        }

        distance_one = GoogleDistanceApi().get_distance(origin=origin, destination=middle_dict)
        distance_two = GoogleDistanceApi().get_distance(origin=middle_dict, destination=destination)

        return {
            "middle": middle,
            "distance": distance_one.distance + distance_two.distance
        }

    @staticmethod
    def get_middle_location_by_code(code: str) -> dict:
        """

            :param code:
            :return:
        """

        try:
            middle_location = MiddleLocation.objects.select_related(
                "address__province__country"
            ).get(code=code, is_available=True)
        except ObjectDoesNotExist as e:
            return {}

        return middle_location.get_ship_dict

    def get_middle_location(self, origin: dict, destination: dict) -> dict:
        """

            :param origin:
            :param destination:
            :return:
        """

        if destination["province"] in ["AB", "BC", "SK", "MB", "NT", "YT"]:
            # WEST
            eliminate = ["QC", "ON", "PE", "NS", "NL", "NB"]
        elif destination["province"] in ["QC", "ON", "PE", "NS", "NL", "NB"]:
            # EAST
            eliminate = ["BC", "SK", "MB", "NT", "YT"]
        else:
            eliminate = []

        middles = MiddleLocation.objects.select_related(
            "address__province__country"
        ).filter(is_available=True).exclude(address__province__code__in=eliminate)

        if not middles:
            return {}

        greenlets = [gevent.Greenlet.spawn(self._get_distance, origin, middle, destination) for middle in middles]
        gevent.joinall(greenlets)
        middle_data = [greenlet.get() for greenlet in greenlets]

        middle_location = self._get_shortest_middle_location(middle_data=middle_data)

        return middle_location.get_ship_dict
