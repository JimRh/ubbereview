"""
    Title: Pickup Validate
    Description: This file will contain all functions that will validate carrier pickup request. If no carrier specific
                 pickup validation exists, defaults will be used.
    Created: August 17, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
import datetime
from typing import Union

import pytz
from django.core.exceptions import ObjectDoesNotExist

from api.exceptions.project import PickupException, ViewException
from api.models import CarrierPickupRestriction, City


class PickupValidate:
    _default_min_start_time = "07:00"
    _default_max_start_time = "16:00"
    _default_min_end_time = "09:00"
    _default_max_end_time = "18:00"
    _default_pickup_window = 2
    _default_future_pickup = 14
    _default_same_day_pickup = "14:00"
    _errors = []

    def __init__(self, pickup_request: dict):
        self._pickup_request = copy.deepcopy(pickup_request)

    @staticmethod
    def _check_timezone(timezone: str) -> bool:
        """
            Check whether the timezone is a real timezone.
            :return: None
        """

        return timezone in pytz.all_timezones_set

    def _get_pickup_restriction(self) -> Union[CarrierPickupRestriction, None]:
        """
            Get carrier specific pickup restriction or return none for defaults.
            :return: CarrierPickupRestriction Object or none.
        """

        try:
            restriction = CarrierPickupRestriction.objects.get(carrier__code=self._pickup_request["carrier_id"])
        except ObjectDoesNotExist:
            return None

        return restriction

    def _check_date(self, max_future_pickup: int) -> None:
        """
            Check the date for a past date and max future date.
            :param max_future_pickup: days in int
            :return: None
        """

        today = datetime.datetime.now().date()
        max_date = today + datetime.timedelta(days=max_future_pickup)

        if self._pickup_request["date"] < today:
            self._errors.append({"date": "Pickup Date cannot be in the past."})
            raise PickupException(
                code="904", message="Pickup Validate: Pickup Date cannot be in the past.", errors=self._errors
            )

        if self._pickup_request["date"] > max_date:
            self._errors.append({"date": f"Pickup Date is too far into the future: Max of {max_future_pickup} Days."})
            raise PickupException(
                code="905", message="Pickup Validate: Pickup Date is too far into the future.", errors=self._errors
            )

    def _check_time(self, min_time: str, max_time: str, time: str) -> None:
        """
            Check whether the time is validate based on the min and max times for each condition.
            :return: None
        """

        if min_time > self._pickup_request[f"{time}_time"]:
            self._errors.append({f"{time}_time": f"Cannot be before Min {time} time with time of {min_time}."})
            raise PickupException(
                code="906", message=f"Pickup Validate: Invalid '{time} time.", errors=self._errors
            )

        if self._pickup_request[f"{time}_time"] > max_time:
            self._errors.append({f"{time}_time": f"Cannot be before Max {time} time with time of {min_time}."})
            raise PickupException(
                code="907", message=f"Pickup Validate: Invalid '{time} time.", errors=self._errors
            )

    def _check_pickup_window(self, pickup_window: int):
        """

            :return:
        """
        start_hours, start_minutes = self._pickup_request["start_time"].split(':')
        end_hours, end_minutes = self._pickup_request["end_time"].split(':')

        hour_diff = float(end_hours) - float(start_hours)
        min_diff = float(f"0.{end_minutes}") - float(f"0.{start_minutes}")

        cal_window = hour_diff + min_diff

        if cal_window < pickup_window:
            self._errors.append({f"pickup_window": f"Window too quick, a min of {pickup_window} hour is required."})
            raise PickupException(
                code="908", message=f"Pickup Validate: Window is too quick.", errors=self._errors
            )

    def _check_timezone_time_against_start_time(self, timezone_now: datetime):
        """

            :param timezone_now:
            :return:
        """
        pickup_date = self._pickup_request["date"].strftime("%Y-%m-%d")
        start_time = self._pickup_request["start_time"]
        timezone_date = timezone_now.strftime("%Y-%m-%d")
        timezone_time = timezone_now.strftime("%H:%M")

        if pickup_date == timezone_date and timezone_time > start_time:
            message = f'Pickup start time: {start_time} is in the past according to timezone time of: {timezone_time}'
            self._errors.append({f"start_time": message})
            raise PickupException(
                code="909", message=f"Pickup Validate: Start Time in the Past.", errors=self._errors
            )

    def _validate_defaults(self):
        """
            Validate Pickup request using defaults.
            :return:
        """

        self._check_date(max_future_pickup=self._default_future_pickup)
        self._check_time(min_time=self._default_min_start_time, max_time=self._default_max_start_time, time="start")
        self._check_time(min_time=self._default_min_end_time, max_time=self._default_max_end_time, time="end")
        self._check_pickup_window(pickup_window=self._default_pickup_window)

    def _validate_carrier(self, restrictions: CarrierPickupRestriction):
        """
            Validate Pickup request using carrier specific pickup restrictions.
            :param restrictions:
            :return:
        """

        self._check_date(max_future_pickup=restrictions.max_pickup_days)
        self._check_time(min_time=restrictions.min_start_time, max_time=restrictions.max_start_time, time="start")
        self._check_time(min_time=restrictions.min_end_time, max_time=restrictions.max_end_time, time="end")
        self._check_pickup_window(pickup_window=restrictions.pickup_window)

    def validate(self) -> bool:
        """
            Validate Pickup request for carrier by using carrier specific restrictions or defaults.
            :return: Success message.
        """
        errors = []

        restrictions = self._get_pickup_restriction()

        try:
            timezone = City().get_timezone(
                name=self._pickup_request["city"],
                province=self._pickup_request["province"],
                country=self._pickup_request["country"]
            )
        except ViewException as e:
            raise PickupException(code=e.code, message=e.message, errors=e.errors)

        if not self._check_timezone(timezone=timezone):
            errors.append({"timezone": "Timezone not found, please use a valid timezone. Ex: America/Edmonton"})
            raise PickupException(
                code="903", message="Pickup Validate: Timezone not found, please use a valid timezone.", errors=errors
            )

        self._check_timezone_time_against_start_time(timezone_now=datetime.datetime.now(tz=pytz.timezone(timezone)))

        if not restrictions:
            self._validate_defaults()

            return True

        self._validate_carrier(restrictions=restrictions)

        return True
