

#  Edmonton, Norman Wells, Yellowknife, Fort Simpson, Hay River, Fort Smith
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection

from api.globals.carriers import BUFFALO_AIRWAYS
from api.models import Airbase


class BuffaloAirbase:

    # NT
    _norman_wells = "X0E0V0"
    _yellowknife = "X1A"
    _yellowknife_full = "X1A2R3"
    _hay_river = "X0E0R9"
    _fort_simpson = "X0E0N0"
    _fort_smith = "X0E0P0"

    # NU
    _cambridge_bay = "X0B0C0"

    # AB
    _edmonton = "T9E0V6"
    _edmonton_airport = "YEG"
    _calgary_airport = "YYC"
    _yellow_airport = "YZF"

    _north = ["NT", "NU"]

    @staticmethod
    def _get_airbase_data(postal_code: str) -> dict:
        """
            Get Airbase information from postal code: X0X0X0.
            :param postal_code:
            :return:
        """
        try:
            airbase = Airbase.objects.get(carrier__code=BUFFALO_AIRWAYS, address__postal_code=postal_code)
        except ObjectDoesNotExist as e:
            connection.close()
            return {}
        return airbase.get_ship_dict

    @staticmethod
    def get_single_base(airport_code: str) -> dict:
        """
            Get Airbase information from airbase code.
            :param airport_code: YEG
            :return:
        """
        try:
            airbase = Airbase.objects.get(carrier__code=BUFFALO_AIRWAYS, code=airport_code)

            return airbase.get_ship_dict
        except ObjectDoesNotExist as e:
            connection.close()
            return {}

    def _alberta(self, postal_code: str) -> dict:
        """
            Get Airbase information based off of postal code.
            :return:
        """
        postal_code = postal_code.replace(" ", "").upper()
        fsa = postal_code[:3]

        if fsa in [
            "T4S", "T0M", "T4H", "T4G", "T1W", "T0C", "T0J", "T1V", "T0L", "T1R", "T1P", "T1G", "T1Z",  "T1M", "T0K",
            "T1Y", "T1A", "T1B", "T1C", "T1H", "T1J", "T1K", "T1L", "T1S", "T1X", "T1Y", "T2A", "T2B", "T2C", "T2E",
            "T2G", "T2H", "T2J", "T2K", "T2L", "T2M", "T2N", "T2P", "T2R", "T2S", "T2T", "T2V", "T2W", "T2X", "T2Y",
            "T2Z", "T3A", "T3B", "T3C", "T3E", "T3G", "T3H", "T3J", "T3K", "T3L", "T3M", "T3N", "T3P", "T3R", "T3S",
            "T3Z", "T4A", "T4B", "T4E", "T4N", "T4P", "T4R", "T3T", "T4C"
        ]:
            # Calgary
            return self.get_single_base(airport_code=self._calgary_airport)

        return self.get_single_base(airport_code=self._edmonton_airport)

    def _northwest_territories(self, postal_code: str) -> dict:
        """
            Get Airbase information based off of postal code.
            :param postal_code: Postal Code: X0X0X0
            :return:
        """

        if postal_code.startswith(self._yellowknife):
            return self._get_airbase_data(postal_code=self._yellowknife_full)
        elif postal_code in [
            "X0E0R9", "X0E0R6", "X0E0R0", "X0E0R2", "X0E0R3", "X0E0R4", "X0E0R6", "X0E0R7", "X0E0R8", "X0E0R9",
            'X0E1G1', "X0E1G2", "X0E1G3", "X0E1G4", "X0E1G5"
        ]:
            return self._get_airbase_data(postal_code=self._norman_wells)
        elif postal_code == self._hay_river:
            return self._get_airbase_data(postal_code=self._hay_river)
        elif postal_code == self._fort_simpson:
            return self._get_airbase_data(postal_code=self._fort_simpson)
        elif postal_code == self._fort_smith:
            return self._get_airbase_data(postal_code=self._fort_smith)

        return {}

    def _nunavut(self, postal_code: str) -> dict:
        """
            Get Airbase information based off of postal code.
            :param postal_code: Postal Code: X0X0X0
            :return:
        """
        if postal_code == self._cambridge_bay:
            return self._get_airbase_data(postal_code=self._cambridge_bay)
        return {}

    def _get_north(self, province: str, postal_code: str) -> dict:
        """
            Get Buffalo northern airbase base off of postal code
            :param province: Province Code: XX
            :param postal_code: Postal Code: X0X0X0
            :return:
        """
        if province == "NT":
            return self._northwest_territories(postal_code=postal_code)
        elif province == "NU":
            return self._nunavut(postal_code=postal_code)

        return {}

    def _get_south(self, postal_code) -> dict:
        """
            Get Buffalo southern airbase.
            :return:
        """
        return self._alberta(postal_code=postal_code)

    def get_yellowknife(self) -> dict:
        return self.get_single_base(airport_code=self._yellow_airport)

    def get_edmonton(self) -> dict:
        return self.get_single_base(airport_code=self._edmonton_airport)

    def get_airbase(self, o_province: str, o_postal_code: str, d_province: str, d_postal_code: str) -> tuple:
        """
            Determine the airbases for a canadian north shipment
            :param o_province: Origin Province: IE: AB, NT
            :param o_postal_code: Canadian Postal Code
            :param d_province: Destination Province: IE: AB, NT
            :param d_postal_code: Canadian Postal Code
            :return: tuple of Dictionaries of Airbases for Origin and Destination
        """

        if o_province in self._north and d_province in self._north:
            # North to North
            mid_origin = self._get_north(province=o_province, postal_code=o_postal_code)
            mid_destination = self._get_north(province=d_province, postal_code=d_postal_code)
            return mid_origin, mid_destination
        elif o_province in self._north and d_province == "AB":
            # North to South
            mid_origin = self._get_north(province=o_province, postal_code=o_postal_code)
            mid_destination = self._get_south(postal_code=d_postal_code)
            return mid_origin, mid_destination
        elif o_province == "AB" and d_province in self._north:
            # South to North
            mid_origin = self._get_south(postal_code=o_postal_code)
            mid_destination = self._get_north(province=d_province, postal_code=d_postal_code)
            return mid_origin, mid_destination

        return {}, {}
