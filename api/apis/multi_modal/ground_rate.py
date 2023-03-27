from django.db import connection
from gevent import Greenlet

from api.apis.carriers.union.api_union_v2 import Union
from api.apis.multi_modal.rate_api import RateAPI


class GroundRate(RateAPI):

    def _make_requests(self) -> None:
        self._responses = []
        union = Union(self._gobox_request)
        rating_thread = Greenlet.spawn(union.rate)

        rating_thread.join()
        response = rating_thread.get()
        responses = {}

        for rate in response:
            carrier_id = rate["carrier_id"]
            rate_list = responses.get(carrier_id, [])
            rate_list.append(rate)
            responses[carrier_id] = rate_list

        for key, value in responses.items():
            self._responses.append((None, value, None))

    def rate(self) -> list:
        exclude_carriers = self._air_list + self._sealift_list
        filtered_carriers = []

        for carrier in self._carrier_id:

            if carrier not in exclude_carriers:
                filtered_carriers.append(carrier)

        self._gobox_request["carrier_id"] = filtered_carriers

        self._make_requests()

        if not self._responses:
            connection.close()
            return []

        connection.close()
        return self._responses
