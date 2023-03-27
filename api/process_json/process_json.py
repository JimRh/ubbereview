import abc
import copy
from decimal import Decimal
from re import sub, IGNORECASE

from django.contrib.auth.models import User

from api.general.convert import Convert
from api.globals.project import DEFAULT_STRING_REGEX
from api.models import SubAccount


class ProcessJson:
    _sig_fig = Decimal("0.01")
    _cubic_meter_contsant = Decimal("1000000")
    _north = ["NT", "NU"]
    _kuujjuaq = "J0M1C0"
    # Values are in CM and KG
    _two_ship_max_weight = Decimal("68.00")
    _two_ship_overall_dimensions = Decimal("365.70")
    _canada_post_max_weight = Decimal("30.00")
    _canada_post_overall_dimensions = Decimal("300.00")

    _ten_thousand = Decimal("10000")

    # _manitoulin_max_weight = Decimal("4535.00")
    # _manitoulin_max_length = Decimal("999.00")
    # _manitoulin_max_width = Decimal("243.00")

    # DG Data
    _battery_un_numbers = {3090, 3091, 3480, 3481}

    def __init__(self, gobox_request: dict, user: User, sub_account: SubAccount):
        self._gobox_request = gobox_request
        self._user = user
        self._sub_account = sub_account
        self._is_metric = gobox_request.get('is_metric', True)
        self._is_dangerous_good = False
        self._is_air_forbidden = False
        self._is_ground_forbidden = False
        self._is_international = False

    @staticmethod
    def _clean_address(address: str) -> str:
        address = sub(DEFAULT_STRING_REGEX, '', address).title()
        address = sub(r'(\s)North(\s)?', r'\g<1>N\g<2>', address, flags=IGNORECASE)
        address = sub(r'(\s)Northeast(\s)?', r'\g<1>NE\g<2>', address, flags=IGNORECASE)
        address = sub(r'(\s)Northwest(\s)?', r'\g<1>NW\g<2>', address, flags=IGNORECASE)
        address = sub(r'(\s)East(\s)?', r'\g<1>E\g<2>', address, flags=IGNORECASE)
        address = sub(r'(\s)Southeast(\s)?', r'\g<1>SE\g<2>', address, flags=IGNORECASE)
        address = sub(r'(\s)Southwest(\s)?', r'\g<1>SW\g<2>', address, flags=IGNORECASE)
        address = sub(r'(\s)South(\s)?', r'\g<1>S\g<2>', address, flags=IGNORECASE)
        address = sub(r'(\s)West(\s)?', r'\g<1>W\g<2>', address, flags=IGNORECASE)
        address = sub(r'(\s)Ave(\s(Nw|Sw|Ne|Se|N|E|S|W))?(\s\Z|\Z)', r'\g<1>Avenue\g<2>', address)
        address = sub(r'(\s)St(\s(Nw|Sw|Ne|Se|N|E|S|W))?(\s\Z|\Z)', r'\g<1>Street\g<2>', address)
        address = sub(r'(\s)Blvd(\s(Nw|Sw|Ne|Se|N|E|S|W))?(\s\Z|\Z)', r'\g<1>Boulevard\g<2>', address)
        address = sub(r'(\s)Rd(\s(Nw|Sw|Ne|Se|N|E|S|W))?(\s\Z|\Z)', r'\g<1>Road\g<2>', address)
        return sub(r'(\s)Dr(\s(Nw|Sw|Ne|Se|N|E|S|W))?(\s\Z|\Z)', r'\g<1>Drive\g<2>', address)

    @staticmethod
    def _clean_city(city: str) -> str:
        return sub(DEFAULT_STRING_REGEX, '', city).title()

    def _convert_package(self, package: dict):
        if self._is_metric:
            package['length'] = Decimal(package['length'])
            package['width'] = Decimal(package['width'])
            package['height'] = Decimal(package['height'])
            package['weight'] = Decimal(package['weight'])
            package['imperial_length'] = Decimal(Convert().cms_to_inches(package['length']))
            package['imperial_width'] = Decimal(Convert().cms_to_inches(package['width']))
            package['imperial_height'] = Decimal(Convert().cms_to_inches(package['height']))
            package['imperial_weight'] = Decimal(Convert().kgs_to_lbs(package['weight']))
        else:
            package['imperial_length'] = Decimal(copy.deepcopy(package['length']))
            package['imperial_width'] = Decimal(copy.deepcopy(package['width']))
            package['imperial_height'] = Decimal(copy.deepcopy(package['height']))
            package['imperial_weight'] = Decimal(copy.deepcopy(package['weight']))
            package['length'] = Decimal(Convert().inches_to_cms(package['length']))
            package['width'] = Decimal(Convert().inches_to_cms(package['width']))
            package['height'] = Decimal(Convert().inches_to_cms(package['height']))
            package['weight'] = Decimal(Convert().lbs_to_kgs(package['weight']))

    def _convert_commodities(self, commodities: dict):

        for commodity in commodities:
            if self._is_metric:
                commodity['total_weight'] = Decimal(commodity['total_weight'])
                commodity['imperial_total_weight'] = Decimal(Convert().kgs_to_lbs(commodity['total_weight']))
            else:
                commodity['imperial_total_weight'] = Decimal(commodity['total_weight'])
                commodity['total_weight'] = Decimal(Convert().lbs_to_kgs(commodity['total_weight']))

    @abc.abstractmethod
    def _check_dg_package(self, package: dict):
        pass

    @abc.abstractmethod
    def _clean_packages(self):
        pass

    @abc.abstractmethod
    def clean(self):
        pass
