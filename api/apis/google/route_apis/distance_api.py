"""
    Title: Google Api Base Class
    Description: This file will contain common functions between the different google apis.
    Created: March 2, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal
from typing import Union

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import connection
from googlemaps import distance_matrix

from api.apis.google.google_api import GoogleApi
from api.exceptions.project import ViewException
from api.models import API, LocationCityAlias, LocationDistance, Province


class GoogleDistanceApi(GoogleApi):
    """
        Class will handle common details between the sub classes.
    """
    _one = 1
    _default = 10

    def __init__(self):
        super(GoogleDistanceApi, self).__init__()
        self._o_city = ""
        self._d_city = ""
        self._o_province = ""
        self._d_province = ""
        self._o_country = ""
        self._d_country = ""

    def _check_city_alias(self) -> None:
        """
            Check Location City Alias Lookup for alias, so that we can reduce api calls
        """
        self._o_city = LocationCityAlias.check_alias(
            alias=self._o_city.lower(),
            province_code=self._o_province,
            country_code=self._o_country
        )

        self._d_city = LocationCityAlias.check_alias(
            alias=self._d_city.lower(),
            province_code=self._d_province,
            country_code=self._d_country
        )

    def _get_location_distance(self) -> Union[LocationDistance, None]:
        """
            Attempt to pull location distance from the database.
            :return: LocationDistance Object or None
        """

        try:
            location = LocationDistance.objects.get(
                origin_city=self._o_city.lower(),
                origin_province__code=self._o_province,
                origin_province__country__code=self._o_country,
                destination_city=self._d_city.lower(),
                destination_province__code=self._d_province,
                destination_province__country__code=self._d_country,
            )
        except ObjectDoesNotExist:
            # Try the reverse direction, as distance should be the same.
            try:
                location = LocationDistance.objects.get(
                    origin_city=self._d_city.lower(),
                    origin_province__code=self._d_province,
                    origin_province__country__code=self._d_country,
                    destination_city=self._o_city.lower(),
                    destination_province__code=self._o_province,
                    destination_province__country__code=self._o_country
                )
            except ObjectDoesNotExist:
                return None

        return location

    def _get_google_distance(self) -> dict:
        """
            Call google distance api to get the distance and duration for the given lane.
            :return: dict with distance and duration.
        """

        data = distance_matrix.distance_matrix(
            client=self._google,
            units="metric",
            origins=f'{self._o_city},{self._o_province}',
            destinations=f'{self._d_city},{self._d_province}'
        )

        if data.get("status", "") != self._STATUS_OK:
            raise ViewException(message=f'Distance Api Error: {data.get("error_message", "")}')

        if data["rows"][0]["elements"][0].get("status") == "ZERO_RESULTS":
            raise ViewException(message=f'Distance Api Error: No distance found.')

        # meters
        distance = data["rows"][0]["elements"][0]["distance"]["value"]
        # seconds
        duration = data["rows"][0]["elements"][0]["duration"]["value"]

        return {
            "distance": distance / self._THOUSAND,
            "duration": duration
        }

    def _save_distance(self, data: dict) -> LocationDistance:
        """
            Save new distance information from the google api for the lane.
            :param data: dict with distance and duration.
            :return: location distance object
        """
        try:
            o_province = Province.objects.get(code=self._o_province, country__code=self._o_country)
        except ObjectDoesNotExist as e:
            raise ViewException(message=f'LocationDistance Error: {str(e)}')

        try:
            d_province = Province.objects.get(code=self._d_province, country__code=self._d_country)
        except ObjectDoesNotExist as e:
            raise ViewException(message=f'LocationDistance Error: {str(e)}')

        if data["distance"] < self._one:
            data["distance"] = self._default

        try:
            location, is_created = LocationDistance.objects.get_or_create(
                origin_city=self._o_city.lower(),
                origin_province=o_province,
                destination_city=self._d_city.lower(),
                destination_province=d_province,
                distance=Decimal(data["distance"]).quantize(self._sig_fig),
                duration=Decimal(data["duration"]).quantize(self._sig_fig)
            )

        except ValidationError as e:
            raise ViewException(message=f'LocationDistance Error: {str(e)}')

        return location

    def get_distance(self, origin: dict, destination: dict) -> Union[LocationDistance, None]:
        """
            Get Distance information for a given origin and destination.
            :return:
        """

        if not API.objects.get(name="DistanceApi").active:
            connection.close()
            raise ViewException(message=f'Distance Api Not Active.')

        self._o_city = origin["city"]
        self._o_province = origin["province"]
        self._o_country = origin["country"]
        self._d_city = destination["city"]
        self._d_province = destination["province"]
        self._d_country = destination["country"]
        self._check_city_alias()

        location = self._get_location_distance()

        if not location:

            data = self._get_google_distance()
            location = self._save_distance(data=data)

        return location
