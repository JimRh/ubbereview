import copy

import gevent
from django.db import connection

from api.apis.carriers.abf_freight.abf_freight_api import ABFFreight
from api.apis.carriers.action_express.action_express_api import ActionExpress
from api.apis.carriers.bbe.bbe_api import BBEApi
from api.apis.carriers.calm_air.calm_air_api import CalmAirApi
from api.apis.carriers.canada_post.canada_post_api import CanadaPostApi
from api.apis.carriers.cargojet.cargojet_api import Cargojet

from api.apis.carriers.day_ross_v2.day_ross_api import DayRossApi
from api.apis.carriers.fedex.fedex_api import FedexApi
from api.apis.carriers.purolator.courier.purolator_api import PurolatorApi
from api.apis.carriers.manitoulin.manitoulin_api import ManitoulinApi
from api.apis.carriers.rate_sheets.rate_sheet_api import RateSheetApi
from api.apis.carriers.skyline.skyline_api_v3 import SkylineApi
from api.apis.carriers.tst_cf_express.tst_cf_express_api import TSTCFExpressApi
from api.apis.carriers.twoship.twoship_api import TwoShipApi
from api.apis.carriers.ubbe_ml.ubbe_ml_api import UbbeMLApi
from api.apis.carriers.yrc.yrc_api import YRCFreight
from api.exceptions.project import ViewException
from api.globals.carriers import (
    TWO_SHIP_CARRIERS,
    SKYLINE_CARRIERS,
    RATE_SHEET_CARRIERS,
    CAN_POST,
    SAMEDAY,
    DAY_N_ROSS,
    SEALIFT_CARRIERS,
    BBE,
    FEDEX,
    TST,
    CALM_AIR,
    PUROLATOR,
    UBBE_ML,
    ACTION_EXPRESS,
    CARGO_JET,
    YRC,
    ABF_FREIGHT,
    MANITOULIN,
)


class Union:
    def __init__(self, gobox_request: dict) -> None:
        self.gobox_request = gobox_request

    def _rate_call(self) -> list:
        (
            two_ship,
            skyline,
            rate_sheet,
            sealift,
            canadapost,
            day_ross,
            sameday,
            bbe,
            tst,
            calm_air,
            puro,
            fedex,
            ml_carrier,
            action,
            cargojet,
            yrc,
            abf,
            man,
        ) = self._split()
        apis = []

        if two_ship["carrier_id"]:
            apis.append(TwoShipApi(ubbe_request=two_ship))
        if skyline["carrier_id"]:
            apis.append(SkylineApi(ubbe_request=skyline))
        if rate_sheet["carrier_id"]:
            apis.append(RateSheetApi(ubbe_request=rate_sheet, is_sealift=False))
        if sealift["carrier_id"]:
            apis.append(RateSheetApi(ubbe_request=sealift, is_sealift=True))
        if canadapost["carrier_id"]:
            apis.append(CanadaPostApi(canadapost))
        if day_ross["carrier_id"] == [DAY_N_ROSS]:
            day_ross["carrier_id"] = DAY_N_ROSS
            apis.append(DayRossApi(ubbe_request=day_ross))
        if sameday["carrier_id"] == [SAMEDAY]:
            sameday["carrier_id"] = SAMEDAY
            apis.append(DayRossApi(ubbe_request=sameday))
        if bbe["carrier_id"] == [BBE]:
            apis.append(BBEApi(ubbe_request=bbe))
        if fedex["carrier_id"] == [FEDEX]:
            apis.append(FedexApi(ubbe_request=fedex))
        if tst["carrier_id"] == [TST]:
            apis.append(TSTCFExpressApi(ubbe_request=tst))
        if calm_air["carrier_id"]:
            apis.append(CalmAirApi(ubbe_request=calm_air))
        if puro["carrier_id"]:
            apis.append(PurolatorApi(ubbe_request=puro))
        if ml_carrier["carrier_id"]:
            apis.append(UbbeMLApi(ubbe_request=ml_carrier))
        if action["carrier_id"]:
            apis.append(ActionExpress(ubbe_request=action))
        if cargojet["carrier_id"]:
            apis.append(Cargojet(ubbe_request=cargojet))
        if yrc["carrier_id"]:
            apis.append(YRCFreight(ubbe_request=yrc))
        if abf["carrier_id"]:
            apis.append(ABFFreight(ubbe_request=abf))
        if man["carrier_id"]:
            apis.append(ManitoulinApi(ubbe_request=man))

        greenlets = [gevent.Greenlet.spawn(api.rate) for api in apis]
        gevent.joinall(greenlets)
        responses = [greenlet.get() for greenlet in greenlets]

        return responses

    def _split(self) -> tuple:
        two_ship = copy.deepcopy(self.gobox_request)
        two_ship["carrier_id"] = [
            carrier
            for carrier in two_ship["carrier_id"]
            if carrier in TWO_SHIP_CARRIERS
        ]

        skyline = copy.deepcopy(self.gobox_request)
        skyline["carrier_id"] = [
            carrier for carrier in skyline["carrier_id"] if carrier in SKYLINE_CARRIERS
        ]

        rate_sheet = copy.deepcopy(self.gobox_request)
        rate_sheet["carrier_id"] = [
            carrier
            for carrier in rate_sheet["carrier_id"]
            if carrier in RATE_SHEET_CARRIERS
        ]

        sealift = copy.deepcopy(self.gobox_request)
        sealift["carrier_id"] = [
            carrier for carrier in sealift["carrier_id"] if carrier in SEALIFT_CARRIERS
        ]

        canadapost = copy.deepcopy(self.gobox_request)
        canadapost["carrier_id"] = [
            carrier for carrier in canadapost["carrier_id"] if carrier == CAN_POST
        ]

        day_ross = copy.deepcopy(self.gobox_request)
        day_ross["carrier_id"] = [
            carrier for carrier in day_ross["carrier_id"] if carrier == DAY_N_ROSS
        ]

        sameday = copy.deepcopy(self.gobox_request)
        sameday["carrier_id"] = [
            carrier for carrier in sameday["carrier_id"] if carrier == SAMEDAY
        ]

        bbe = copy.deepcopy(self.gobox_request)
        bbe["carrier_id"] = [carrier for carrier in bbe["carrier_id"] if carrier == BBE]

        fedex = copy.deepcopy(self.gobox_request)
        fedex["carrier_id"] = [
            carrier for carrier in fedex["carrier_id"] if carrier == FEDEX
        ]

        tst = copy.deepcopy(self.gobox_request)
        tst["carrier_id"] = [carrier for carrier in tst["carrier_id"] if carrier == TST]

        calm_air = copy.deepcopy(self.gobox_request)
        calm_air["carrier_id"] = [
            carrier for carrier in calm_air["carrier_id"] if carrier == CALM_AIR
        ]

        puro = copy.deepcopy(self.gobox_request)
        puro["carrier_id"] = [
            carrier for carrier in puro["carrier_id"] if carrier == PUROLATOR
        ]

        ml_carrier = copy.deepcopy(self.gobox_request)
        ml_carrier["carrier_id"] = [
            carrier for carrier in ml_carrier["carrier_id"] if carrier == UBBE_ML
        ]

        action = copy.deepcopy(self.gobox_request)
        action["carrier_id"] = [
            carrier for carrier in action["carrier_id"] if carrier == ACTION_EXPRESS
        ]

        cargojet = copy.deepcopy(self.gobox_request)
        cargojet["carrier_id"] = [
            carrier for carrier in cargojet["carrier_id"] if carrier == CARGO_JET
        ]

        yrc = copy.deepcopy(self.gobox_request)
        yrc["carrier_id"] = [carrier for carrier in yrc["carrier_id"] if carrier == YRC]

        abf = copy.deepcopy(self.gobox_request)
        abf["carrier_id"] = [
            carrier for carrier in abf["carrier_id"] if carrier == ABF_FREIGHT
        ]

        man = copy.deepcopy(self.gobox_request)
        man["carrier_id"] = [
            carrier for carrier in man["carrier_id"] if carrier == MANITOULIN
        ]

        return (
            two_ship,
            skyline,
            rate_sheet,
            sealift,
            canadapost,
            day_ross,
            sameday,
            bbe,
            tst,
            calm_air,
            puro,
            fedex,
            ml_carrier,
            action,
            cargojet,
            yrc,
            abf,
            man,
        )

    def rate(self) -> list:
        try:
            rates = self._rate_call()
        except ViewException:
            connection.close()
            raise
        all_rates = []

        for rate in rates:
            all_rates += rate

        connection.close()
        return all_rates
