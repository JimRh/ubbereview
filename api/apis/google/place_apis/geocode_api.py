"""
    Title: Google Geocode Api Class
    Description: This file will get coordinates for a given address location and return the latitude, longitude,
                 and place_id.
    Created: August 20, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.db import connection
from googlemaps import geocoding

from api.apis.google.google_api import GoogleApi
from api.exceptions.project import ViewException
from api.models import API


class GoogleGeocodeApi(GoogleApi):
    """
            Class will handle common details between the sub classes.
        """

    @staticmethod
    def _get_locality(address_components: list) -> tuple:
        """
            Get locality for geocode, means the city.
            :param address_components: Address component list.
            :return: tuple of longname.
        """
        long_name = ""
        short_name = ""

        for component in address_components:

            if "locality" in component["types"]:
                long_name = component["long_name"]
                short_name = component["short_name"]

        return long_name, short_name

    def _get_google_geocode(self, address: str, country: str) -> dict:
        """
            Call google geocode api to get coordinates for a given address location and return them.
            :return: dict with coordinates.
        """

        data = geocoding.geocode(
            client=self._google,
            address=address,
            components={
                "country": country
            }
        )

        if not data:
            raise ViewException(message=f'No geocode found for location {address}')

        results = data[0]

        if not results["geometry"]:
            raise ViewException(message=f'No geometry found for location {address}.')

        latitude = results["geometry"]["location"]["lat"]
        longitude = results["geometry"]["location"]["lng"]

        long_name, short_name = self._get_locality(address_components=results["address_components"])

        return {
            "google_place_id": results["place_id"],
            "latitude": latitude,
            "longitude": longitude,
            "long_name": long_name.lower(),
            "short_name": short_name.lower()
        }

    def get_coordinates(self, city: str, province: str, country: str) -> dict:
        """
            Get Geocode information for a given address.
            :return:
        """

        if not API.objects.get(name="GoogleGeocodeApi").active:
            connection.close()
            raise ViewException(message=f'Google Geocode Api Not Active.')

        try:
            data = self._get_google_geocode(address=f"{city} {province}", country=country)
        except ViewException as e:
            raise ViewException(message=f'Google Geocode Api Error: {e.message}')

        return data
