import copy
from decimal import Decimal


class RateAPI:
    _sig_fig = Decimal("0.01")

    def __init__(self, gobox_request: dict) -> None:
        self._gobox_request = copy.deepcopy(gobox_request)
        self._user = copy.deepcopy(gobox_request["objects"]["user"])
        self.sub_account = copy.deepcopy(gobox_request["objects"]["sub_account"])
        self._air_list = copy.deepcopy(gobox_request["objects"]["air_list"])
        self._ltl_list = copy.deepcopy(gobox_request["objects"]["ltl_list"])
        self._ftl_list = copy.deepcopy(gobox_request["objects"]["ftl_list"])
        self._courier_list = copy.deepcopy(gobox_request["objects"]["courier_list"])
        self._sealift_list = copy.deepcopy(gobox_request["objects"]["sealift_list"])

        self._origin = self._gobox_request["origin"]
        self._destination = self._gobox_request["destination"]
        self._carrier_id = self._gobox_request.get("carrier_id", [])
        self._is_dg = self._gobox_request["is_dangerous_goods"]

    def _apply_markup(self, data: dict, multiplier: Decimal) -> None:
        data['freight'] = (data['freight'] * multiplier).quantize(self._sig_fig)
        data['surcharge'] = (data['surcharge'] * multiplier).quantize(self._sig_fig)
        data['tax'] = (data['tax'] * multiplier).quantize(self._sig_fig)
        data['total'] = (data['total'] * multiplier).quantize(self._sig_fig)
