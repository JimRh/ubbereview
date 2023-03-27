import math
from datetime import datetime, timedelta
from typing import Union

from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class OnDemandPickupTime(SOAPObj):
    _hour_twelve = datetime(year=1, month=1, day=1, hour=12).time()
    _hour_sixteen = datetime(year=1, month=1, day=1, hour=16).time()
    _hour = timedelta(hours=1)
    _thirty_days = timedelta(days=30)

    def __init__(self, pickup_datetime: dict) -> None:
        self._pickup_datetime = pickup_datetime
        self._clean()

    # Override
    def _clean(self) -> None:
        start = datetime.strptime(self._pickup_datetime["start_time"], "%H:%M")
        start = start.replace(minute=math.ceil(start.minute / 15) * 15)

        if start.minute > 59:
            self._pickup_datetime["start_time"] = datetime(
                year=2000, month=1, day=1, hour=start.hour + 1
            ).strftime("%H:%M")
        else:
            self._pickup_datetime["start_time"] = datetime(
                year=2000, month=1, day=1, hour=start.hour
            ).strftime("%H:%M")

        end = datetime.strptime(self._pickup_datetime["end_time"], "%H:%M")
        end = end.replace(minute=math.ceil(end.minute / 15) * 15)

        if end.minute > 59:
            self._pickup_datetime["end_time"] = datetime(
                year=2000, month=1, day=1, hour=end.hour + 1
            ).strftime("%H:%M")
        else:
            self._pickup_datetime["end_time"] = datetime(
                year=2000, month=1, day=1, hour=end.hour
            ).strftime("%H:%M")

    # Override
    def data(self) -> Union[list, dict]:
        start_time = datetime.strptime(
            self._pickup_datetime["start_time"], "%H:%M"
        ).time()
        end_time = datetime.strptime(self._pickup_datetime["end_time"], "%H:%M").time()
        min_time = (
            datetime.now().replace(hour=12, minute=0, second=0, microsecond=0).time()
        )
        max_time = (
            datetime.now().replace(hour=17, minute=0, second=0, microsecond=0).time()
        )

        return {
            "date": self._pickup_datetime["date"].strftime("%Y-%m-%d"),
            "preferred-time": max(min_time, start_time).strftime("%H:%M"),
            "closing-time": min(max_time, end_time).strftime("%H:%M"),
        }
