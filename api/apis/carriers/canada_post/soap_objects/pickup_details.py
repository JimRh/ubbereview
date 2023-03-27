from datetime import datetime
from typing import Union

from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class PickupDetails(SOAPObj):
    def __init__(self, date: str) -> None:
        self._date = datetime.strptime(date, "%Y-%m-%d")

    # Override
    def _clean(self) -> None:
        pass

    # Override
    def data(self) -> Union[list, dict]:
        return {"date": self._date.strftime("%Y-%m-%d")}
