import copy

from django.core.exceptions import ObjectDoesNotExist

from api.background_tasks.emails import CeleryEmail
from api.models import Dispatch


class RateSheetEmail:
    def __init__(self, ubbe_request: dict) -> None:
        self._ubbe_request = copy.deepcopy(ubbe_request)

        if "dg_service" in self._ubbe_request:
            del self._ubbe_request["dg_service"]

        if "objects" in self._ubbe_request:
            del self._ubbe_request["objects"]

        if "other_legs" in self._ubbe_request:
            del self._ubbe_request["other_legs"]

    def _clean_data(self) -> None:

        if "leg" in self._ubbe_request:
            del self._ubbe_request["leg"]

        for request_package in self._ubbe_request["packages"]:
            if request_package["is_dangerous_good"]:
                if "dg_object" in request_package:
                    del request_package["dg_object"]

    def _get_dispatch(self) -> Dispatch:
        """
        Get dispatch for carrier city terminal, if none exist get the default one.
        :return:
        """

        try:
            dispatch = Dispatch.objects.get(
                carrier__code=self._ubbe_request["carrier_id"], location=self._ubbe_request["origin"]["city"]
            )
        except ObjectDoesNotExist:
            dispatch = Dispatch.objects.get(carrier__code=self._ubbe_request["carrier_id"], is_default=True)

        return dispatch

    def manual_email(self) -> None:
        self._clean_data()

        if "carrier_email" not in self._ubbe_request:
            dispatch = self._get_dispatch()
            self._ubbe_request["carrier_email"] = dispatch.email

        # Do not send the email
        is_do_not_ship = self._ubbe_request.get("do_not_ship", False)
        # Do not send the email
        is_do_not_pickup = self._ubbe_request.get("do_not_pickup", False)
        is_send_email = False

        if is_do_not_pickup:
            return

        if not is_do_not_ship and not is_do_not_pickup:
            is_send_email = True
        elif is_do_not_ship and not is_do_not_pickup:
            is_send_email = True

        if is_send_email:
            if self._ubbe_request.get("is_dangerous_goods", False):
                CeleryEmail().rate_sheet_email(copy.deepcopy(self._ubbe_request))
            else:
                CeleryEmail().rate_sheet_email.delay(copy.deepcopy(self._ubbe_request))
