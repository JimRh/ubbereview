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
from googlemaps import timezone

from api.apis.google.google_api import GoogleApi
from api.apis.google.place_apis.geocode_api import GoogleGeocodeApi
from api.exceptions.project import ViewException
from api.models import API


class GoogleTimezoneApi(GoogleApi):
    """
            Class will handle common details between the sub classes.
        """

    def _get_google_timezone(self, location: str) -> dict:
        """
            Call google timezone api to get timezone information for a given address location and return them.
            :return: dict with timezone.
        """

        data = timezone.timezone(
            client=self._google,
            location=location
        )

        if not data:
            raise ViewException(message=f'No timezone found for location {location}')

        if data.get("status", "") != self._STATUS_OK:
            raise ViewException(message=f'{data.get("error_message", "")}')

        return {
            "timezone_dst_off_set": data["dstOffset"],
            "timezone_raw_off_set": data["rawOffset"],
            "timezone": data["timeZoneId"],
            "timezone_name": data["timeZoneName"]
        }

    def get_timezone(self, city: str, province: str, country: str) -> dict:
        """
            Get timezone information for a given address.
            :return:
        """

        if not API.objects.get(name="GoogleTimezoneApi").active:
            connection.close()
            raise ViewException(message=f'Google timezone Api Not Active.')

        try:
            cords = GoogleGeocodeApi().get_coordinates(city=city, province=province, country=country)
        except ViewException as e:
            raise ViewException(message=f'Google timezone Api Error: {e.message}')

        try:
            data = self._get_google_timezone(location=f'{cords["latitude"]},{cords["longitude"]}')
        except ViewException as e:
            raise ViewException(message=f'Google timezone Api Error: {e.message}')

        data.update(cords)

        return data
