
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection

from api.globals.carriers import PERIMETER_AIR
from api.models import Airbase


class PerimeterAirbase:

    # MB
    _winnipeg = "R3H0T7"
    _winnipeg_airport = "YWG"

    _thompson = "R8N1M9"
    _thompson_airport = "YTH"

    _brochet = "R0B0B0"
    _brochet_airport = "YBT"

    _cross_lake = "X0A0C0"
    _cross_lake_airport = "YCR"

    _gods_lake_narrows = "R0B0M0"
    _gods_lake_narrows_airport = "YGO"

    _gods_river = "R0B0N0"
    _gods_river_airport = "ZGI"

    _island_lake = "R0B2H0"
    _island_lake_airport = "YIV"

    _lac_brochet = "R0B2E0"
    _lac_brochet_airport = "XLB"

    _norway_house = "R0B1B0"
    _norway_house_airport = "YNE"

    _oxford_house = "R0B1C0"
    _oxford_house_airport = "YOH"

    _red_sucker_lake = "R0B1H0"
    _red_sucker_lake_airport = "YRS"

    _shamattawa = "R0B1K0"
    _shamattawa_airport = "ZTM"

    _south_indian_lake = "R0B1N0"
    _south_indian_lake_airport = "XSI"

    _st_theresa_point = "R0B1J0"
    _st_theresa_point_airport = "YST"

    _tadoule_lake = "R0B2C0"
    _tadoule_lake_airport = "XTL"

    _waasagamack = "R0B1Z0"
    _waasagamack_airport = "WGK"

    _york_landing = "R0B2B0"
    _york_landing_airport = "ZAC"

    # ON
    _deer_lake = "P0V1N0"
    _deer_lake_airport = "YVZ"

    _north_spirit_lake = "P0V2G0"
    _north_spirit_lake_airport = "YNO"

    _pikangikum = "P0V2L0"
    _pikangikum_airport = "YPM"

    _round_lake = "P0J2Y0"
    _round_lake_airport = "ZRI"

    _sachigo_lake = "P0V2P0"
    _sachigo_lake_airport = "ZPB"

    _sandy_lake = "P0V1V0"
    _sandy_lake_airport = "ZSJ"

    _sioux_lookout = "P8T1G7"
    _sioux_lookout_airport = "YXL"

    _thunder_bay = "P7E3N9"
    _thunder_bay_airport = "YQT"

    @staticmethod
    def _get_airbase_data(postal_code: str) -> dict:
        """
            Get Airbase information from postal code: X0X0X0.
            :param postal_code:
            :return:
        """
        try:
            airbase = Airbase.objects.get(carrier__code=PERIMETER_AIR, address__postal_code=postal_code)
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
            airbase = Airbase.objects.get(carrier__code=PERIMETER_AIR, code=airport_code)

            return airbase.get_ship_dict
        except ObjectDoesNotExist as e:
            connection.close()
            return {}

    def _manitoba(self, postal_code: str) -> dict:
        """

            :param postal_code:
            :return:
        """
        fsa = postal_code[:3]

        if fsa in [
            "R4A", "R2E", "R2P", "R2V", "R2G", "R2R", "R2X", "R2W", "R2L", "R2K", "R3W", "R2C", "R2Y", "R3H", "R3E",
            "R3A", "R3B", "R3C", "R3G", "R3J", "R3K", "R2H", "R2J", "R2M", "R3X", "R2N", "R3V", "R3T", "R3Y", "R3P",
            "R3S", "R3R", "R3N", "R3M", "R3L", "R4K", "R0K", "R0M", "R1N", "R0J", "R7N", "R0L", "R0C", "R4L", "R0H",
            "R0G", "R6M", "R6W", "R5A", "R5G", "R0A", "R5H", "R1A", "R0E", "R7C", "R7A", "R7B", "R4H", "R4J", "R4G",
            "R1C", "R1B", "R5K"
        ]:
            # Winnipeg
            return self.get_single_base(airport_code=self._winnipeg_airport)
        elif postal_code.startswith("R8N"):
            # Thompson
            return self.get_single_base(airport_code=self._thompson_airport)
        elif postal_code == self._brochet:
            return self.get_single_base(airport_code=self._brochet_airport)
        elif postal_code == self._cross_lake:
            return self.get_single_base(airport_code=self._cross_lake_airport)
        elif postal_code == self._gods_lake_narrows:
            return self.get_single_base(airport_code=self._gods_lake_narrows_airport)
        elif postal_code == self._gods_river:
            return self.get_single_base(airport_code=self._gods_river_airport)
        elif postal_code in [self._island_lake, "ROB0T0"]:
            return self.get_single_base(airport_code=self._island_lake_airport)
        elif postal_code == self._lac_brochet:
            return self.get_single_base(airport_code=self._lac_brochet_airport)
        elif postal_code == self._norway_house:
            return self.get_single_base(airport_code=self._norway_house_airport)
        elif postal_code == self._oxford_house:
            return self.get_single_base(airport_code=self._oxford_house_airport)
        elif postal_code == self._red_sucker_lake:
            return self.get_single_base(airport_code=self._red_sucker_lake_airport)
        elif postal_code == self._shamattawa:
            return self.get_single_base(airport_code=self._shamattawa_airport)
        elif postal_code == self._south_indian_lake:
            return self.get_single_base(airport_code=self._south_indian_lake_airport)
        elif postal_code == self._st_theresa_point:
            return self.get_single_base(airport_code=self._st_theresa_point_airport)
        elif postal_code == self._tadoule_lake:
            return self.get_single_base(airport_code=self._tadoule_lake_airport)
        elif postal_code == self._waasagamack:
            return self.get_single_base(airport_code=self._waasagamack_airport)
        elif postal_code == self._york_landing:
            return self.get_single_base(airport_code=self._york_landing_airport)

        return {}

    def _ontario(self, postal_code: str) -> dict:

        fsa = postal_code[:3]

        if postal_code == self._deer_lake:
            return self.get_single_base(airport_code=self._deer_lake_airport)
        elif postal_code == self._north_spirit_lake:
            return self.get_single_base(airport_code=self._north_spirit_lake_airport)
        elif postal_code == self._pikangikum:
            return self.get_single_base(airport_code=self._pikangikum_airport)
        elif postal_code == self._round_lake:
            return self.get_single_base(airport_code=self._round_lake_airport)
        elif postal_code == self._sachigo_lake:
            return self.get_single_base(airport_code=self._sachigo_lake_airport)
        elif postal_code == self._sandy_lake:
            return self.get_single_base(airport_code=self._sandy_lake_airport)
        elif fsa == "P8T":
            # Sioux Lookout
            return self.get_single_base(airport_code=self._sioux_lookout_airport)
        elif postal_code in ["P4N", "P4P", "P4R", "P5A", "P5E", "P5N", "P5A", "P6A", "P6B", "P6C", "P6", "P7A", "P7B",
                             "P7C", "P7E", "P7G", "P7J", "P7K", "P7L", "P7N", "P7T", "P9A", "P9N", "P0L", "P0N", "P0S",
                             "P0T", "P0V", "P0W", "P0X", "P0Y"]:
            # Thunder Bay
            return self.get_single_base(airport_code=self._thunder_bay_airport)

        return {}

    def _get_airbase_single(self, province: str, postal_code: str) -> dict:
        postal_code = postal_code.replace(" ", "").upper()

        if province == "AB":
            pass
        elif province == "BC":
            pass
        elif province == "MB":
            return self._manitoba(postal_code=postal_code)
        elif province == "NB":
            pass
        elif province == "NL":
            pass
        elif province == "NS":
            pass
        elif province == "NT":
            pass
        elif province == "NU":
            pass
        elif province == "ON":
            return self._ontario(postal_code=postal_code)
        elif province == "PE":
            pass
        elif province == "QC":
            pass
        elif province == "SK":
            pass
        elif province == "YT":
            pass

        return {}

    def get_airbase(self, o_province: str, o_postal_code: str, d_province: str, d_postal_code: str) -> tuple:
        """
            Determine the airbases for a Perimeter Air Shipment
            :param o_province: Origin Province: IE: AB, NT
            :param o_postal_code: Canadian Postal Code
            :param d_province: Destination Province: IE: AB, NT
            :param d_postal_code: Canadian Postal Code
            :return: tuple of Dictionaries of Airbases for Origin and Destination
        """

        if o_province.upper() not in ["MB", "ON"] and d_province.upper() in ["MB", "ON"]:
            mid_origin = self.get_single_base(airport_code=self._winnipeg_airport)
            mid_destination = self._get_airbase_single(province=d_province, postal_code=d_postal_code)
        else:
            mid_origin = self._get_airbase_single(province=o_province, postal_code=o_postal_code)
            mid_destination = self._get_airbase_single(province=d_province, postal_code=d_postal_code)

        return mid_origin, mid_destination
