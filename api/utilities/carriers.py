import copy

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet

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
from api.cache_lookups.carrier_cache import CarrierCache
from api.exceptions.project import ViewException
from api.globals.carriers import SKYLINE_CARRIERS, TWO_SHIP_CARRIERS, RATE_SHEET_CARRIERS, SEALIFT_CARRIERS, \
    DAY_N_ROSS, SAMEDAY, BBE, FEDEX, CAN_POST, TST, CALM_AIR, PUROLATOR, ACTION_EXPRESS, UBBE_ML, CARGO_JET, YRC, \
    ABF_FREIGHT, MANITOULIN
from api.models import SubAccount, CarrierAccount


class CarrierUtility:

    @staticmethod
    def get_ship_api(data: dict):
        carrier = data["carrier_id"]
        service_code = data["service_code"]

        if carrier in SKYLINE_CARRIERS:
            return SkylineApi(ubbe_request=data)
        if carrier in TWO_SHIP_CARRIERS:
            return TwoShipApi(ubbe_request=data)
        if carrier in RATE_SHEET_CARRIERS:
            return RateSheetApi(ubbe_request=data)
        if carrier in SEALIFT_CARRIERS:
            return RateSheetApi(ubbe_request=data)
        if carrier == CAN_POST:
            return CanadaPostApi(ubbe_request=data)
        if carrier in (DAY_N_ROSS, SAMEDAY):
            if service_code == "LTL":
                return RateSheetApi(ubbe_request=data)
            else:
                return DayRossApi(ubbe_request=data)
        if carrier == BBE:
            return BBEApi(ubbe_request=data)
        if carrier == FEDEX:
            return FedexApi(ubbe_request=data)
        if carrier == TST:
            return TSTCFExpressApi(ubbe_request=data)
        if carrier == CALM_AIR:
            return CalmAirApi(ubbe_request=data)
        if carrier == PUROLATOR:
            return PurolatorApi(ubbe_request=data)
        if carrier == UBBE_ML:
            return UbbeMLApi(ubbe_request=data)
        if carrier == ACTION_EXPRESS:
            return ActionExpress(ubbe_request=data)
        if carrier == CARGO_JET:
            return Cargojet(ubbe_request=data)
        if carrier == YRC:
            return YRCFreight(ubbe_request=data)
        if carrier == ABF_FREIGHT:
            return ABFFreight(ubbe_request=data)
        if carrier == MANITOULIN:
            return ManitoulinApi(ubbe_request=data)

        raise ViewException({"ship.carrier.error": "carrier " + str(carrier) + " is not valid"})

    @staticmethod
    def get_ltl() -> list:
        """
            Get LTL & FTL carrier list
            :return: carrier accounts
        """

        return CarrierCache().get_carrier_list_mode("LT")

    @staticmethod
    def get_ftl() -> list:
        """
            Get LTL & FTL carrier list
            :return: carrier accounts
        """

        return CarrierCache().get_carrier_list_mode("FT")

    @staticmethod
    def get_courier() -> list:
        """
            Get Courier carrier list
            :return: carrier accounts
        """

        return CarrierCache().get_carrier_list_mode("CO")

    @staticmethod
    def get_air() -> list:
        """
            Get Air carrier list
            :return: carrier accounts
        """

        return CarrierCache().get_carrier_list_mode("AI")

    @staticmethod
    def get_sealift() -> list:
        """
            Get Sealift carrier list
            :return: carrier accounts
        """

        return CarrierCache().get_carrier_list_mode("SE")

    @staticmethod
    def _get_account(accounts: QuerySet, sub_account_carriers: QuerySet, carrier: int) -> CarrierAccount:
        """
            Get carrier account for carrier id.
            :param sub_account: api account
            :param carrier:
            :return: carrier accounts
        """

        try:
            # Get account for sub account
            carrier_account = sub_account_carriers.get(carrier__code=carrier)
        except ObjectDoesNotExist:
            # Get default account
            carrier_account = accounts.get(carrier__code=carrier)

        return carrier_account

    @staticmethod
    def _get_default_carrier_accounts() -> QuerySet:
        return CarrierAccount.objects.select_related(
            "carrier",
            'api_key',
            'username',
            'password',
            'account_number',
            'contract_number',
        ).filter(subaccount__is_default=True)

    @staticmethod
    def _get_sub_account_carrier_accounts(sub_account: SubAccount) -> QuerySet:
        return CarrierAccount.objects.select_related(
            "subaccount",
            "carrier",
            'api_key',
            'username',
            'password',
            'account_number',
            'contract_number',
        ).filter(subaccount=sub_account)

    def get_carrier_accounts(self, sub_account: SubAccount, carrier_list: list) -> dict:
        """
            Get all carrier accounts for a rate request before going to treads.
            :param sub_account: api account
            :param carrier_list: carrier id list
            :return: dictionary of carrier accounts
        """
        carrier_accounts = {}
        copied_carriers = copy.deepcopy(carrier_list)

        accounts = self._get_default_carrier_accounts()
        sub_account_carriers = self._get_sub_account_carrier_accounts(sub_account=sub_account)

        for carrier_id in copied_carriers:

            try:
                carrier_account = self._get_account(
                    accounts=accounts,
                    sub_account_carriers=sub_account_carriers,
                    carrier=carrier_id
                )
            except ObjectDoesNotExist:
                carrier_list.remove(carrier_id)
                continue

            carrier_accounts[carrier_id] = {
                "account": carrier_account,
                "carrier": carrier_account.carrier
            }

        try:
            # Get account for sub account
            bbe_account = accounts.get(carrier__code=BBE)
            carrier_accounts[BBE] = {
                "account": bbe_account,
                "carrier": bbe_account.carrier
            }
        except ObjectDoesNotExist:
            # Get default account
            pass

        return carrier_accounts

    def get_carrier_accounts_ship(self, sub_account: SubAccount, gobox_request: dict) -> tuple:
        """
            Get all carrier accounts for a ship request before going to treads.
            :param sub_account: api account
            :param gobox_request: carrier id list
            :return: dictionary of carrier accounts
        """
        carrier_accounts = {}
        carriers = {}
        accounts = self._get_default_carrier_accounts()
        sub_account_carriers = self._get_sub_account_carrier_accounts(sub_account=sub_account)
        service = gobox_request["service"]

        main_carrier_account = self._get_account(
            accounts=accounts,
            sub_account_carriers=sub_account_carriers,
            carrier=service["carrier_id"]
        )

        carrier_accounts[service["carrier_id"]] = {
            "account": main_carrier_account,
            "carrier": main_carrier_account.carrier
        }
        carriers["m_carrier"] = main_carrier_account.carrier

        if 'pickup' in service:
            p_carrier = service["pickup"]["carrier_id"]
            pickup_carrier_account = self._get_account(
                accounts=accounts,
                sub_account_carriers=sub_account_carriers,
                carrier=p_carrier
            )

            carrier_accounts[p_carrier] = {
                "account": pickup_carrier_account,
                "carrier": pickup_carrier_account.carrier
            }
            carriers["p_carrier"] = pickup_carrier_account.carrier

        if 'delivery' in service:
            d_carrier = service["delivery"]["carrier_id"]
            delivery_carrier_account = self._get_account(
                accounts=accounts,
                sub_account_carriers=sub_account_carriers,
                carrier=d_carrier
            )

            carrier_accounts[d_carrier] = {
                "account": delivery_carrier_account,
                "carrier": delivery_carrier_account.carrier
            }
            carriers["d_carrier"] = delivery_carrier_account.carrier

        return carrier_accounts, carriers
