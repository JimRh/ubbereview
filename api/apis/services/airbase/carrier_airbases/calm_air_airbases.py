
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection

from api.globals.carriers import CALM_AIR
from api.models import Airbase


class CalmAirAirbase:

    # MB
    _winnipeg = "R3H0Z8"
    _winnipeg_airport = "YWG"

    _thompson = "R8N1M9"
    _thompson_airport = "YTH"

    _churchill = "R0B0E0"
    _churchill_airport = "YYQ"

    _the_pas = "R9A1K8"
    _the_pas_airport = "YQD"

    _gillam = "R0B0L0"
    _gillam_airport = "YGX"

    _flin_flon = "R8A0T7"
    _flin_flon_airport = "YFO"

    # NU
    _rankin_inlet = "X0C0G0"
    _rankin_inlet_airport = "YRT"

    _whale_cove = "X0C0J0"
    _whale_cove_airport = "YXN"

    # Repulse Bay
    _naujaat = "X0C0H0"
    _naujaat_airport = "YUT"

    _coral_harbour = "X0C0C0"
    _coral_harbour_airport = "YZS"

    _chesterfield_inlet = "X0C0B0"
    _chesterfield_inlet_airport = "YCS"

    _arviat = "X0C0E0"
    _arviat_airport = "YEK"

    _baker_lake = "X0C0A0"
    _baker_lake_airport = "YBK"

    _sanikiluaq = "X0A0W0"
    _sanikiluaq_airport = "YSK"
    #
    # _taloyoak = "X0C0E0"
    # _taloyoak_airport = "YEK"
    #
    # _gjoa_haven = "X0C0E0"
    # _gjoa_haven_airport = "YEK"
    #
    # _kuggaruk = "X0C0E0"
    # _kuggaruk_airport = "YEK"
    #
    # _pond_inlet = "X0C0E0"
    # _pond_inlet_airport = "YEK"
    #
    # _arctic_bay = "X0C0E0"
    # _arctic_bay_airport = "YEK"
    #
    # _hall_beach = "X0C0E0"
    # _hall_beach_airport = "YEK"
    #
    # _igloolik = "X0C0E0"
    # _igloolik_airport = "YEK"

    @staticmethod
    def _get_airbase_data(postal_code: str) -> dict:
        """
            Get Airbase information from postal code: X0X0X0.
            :param postal_code:
            :return:
        """
        try:
            airbase = Airbase.objects.get(carrier__code=CALM_AIR, address__postal_code=postal_code)
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
            airbase = Airbase.objects.get(carrier__code=CALM_AIR, code=airport_code)

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
        elif postal_code == self._churchill:
            return self.get_single_base(airport_code=self._churchill_airport)
        elif postal_code == self._the_pas:
            return self.get_single_base(airport_code=self._the_pas_airport)
        elif postal_code == self._gillam:
            return self.get_single_base(airport_code=self._gillam_airport)
        elif postal_code == self._flin_flon:
            return self.get_single_base(airport_code=self._flin_flon_airport)

        return {}

    def _nunavut(self, postal_code: str) -> dict:
        """

            :param postal_code:
            :return:
        """

        if postal_code == self._rankin_inlet:
            return self.get_single_base(airport_code=self._rankin_inlet_airport)
        elif postal_code == self._whale_cove:
            return self.get_single_base(airport_code=self._whale_cove_airport)
        elif postal_code == self._naujaat:
            return self.get_single_base(airport_code=self._naujaat_airport)
        elif postal_code == self._coral_harbour:
            return self.get_single_base(airport_code=self._coral_harbour_airport)
        elif postal_code == self._chesterfield_inlet:
            return self.get_single_base(airport_code=self._chesterfield_inlet_airport)
        elif postal_code == self._arviat:
            return self.get_single_base(airport_code=self._arviat_airport)
        elif postal_code == self._baker_lake:
            return self.get_single_base(airport_code=self._baker_lake_airport)
        elif postal_code == self._sanikiluaq:
            return self.get_single_base(airport_code=self._sanikiluaq_airport)

        return {}

    def _get_airbase_single(self, province: str, postal_code: str) -> dict:
        postal_code = postal_code.replace(" ", "").upper()

        if province == "AB":
            # return self.get_single_base(airport_code=self._winnipeg_airport)
            pass
        elif province == "BC":
            # return self.get_single_base(airport_code=self._winnipeg_airport)
            pass
        elif province == "MB":
            return self._manitoba(postal_code=postal_code)
        elif province == "NB":
            # return self.get_single_base(airport_code=self._winnipeg_airport)
            pass
        elif province == "NL":
            # return self.get_single_base(airport_code=self._winnipeg_airport)
            pass
        elif province == "NS":
            # return self.get_single_base(airport_code=self._winnipeg_airport)
            pass
        elif province == "NT":
            pass
        elif province == "NU":
            return self._nunavut(postal_code=postal_code)
        elif province == "ON":
            # return self.get_single_base(airport_code=self._winnipeg_airport)
            pass
        elif province == "PE":
            # return self.get_single_base(airport_code=self._winnipeg_airport)
            pass
        elif province == "QC":
            # return self.get_single_base(airport_code=self._winnipeg_airport)
            pass
        elif province == "SK":
            # return self.get_single_base(airport_code=self._winnipeg_airport)
            pass
        elif province == "YT":
            pass

        return {}

    def get_airbase(self, o_province: str, o_postal_code: str, d_province: str, d_postal_code: str) -> tuple:
        """
            Determine the airbases for a Calm Air Shipment
            :param o_province: Origin Province: IE: AB, NT
            :param o_postal_code: Canadian Postal Code
            :param d_province: Destination Province: IE: AB, NT
            :param d_postal_code: Canadian Postal Code
            :return: tuple of Dictionaries of Airbases for Origin and Destination
        """

        if o_province.upper() not in ["NT", "NU", "MB"]:
            mid_origin = self.get_single_base(airport_code=self._winnipeg_airport)
            mid_destination = self._get_airbase_single(province=d_province, postal_code=d_postal_code)
        elif o_province.upper() == "MB" and d_province.upper() not in ["NT", "NU", "MB"]:
            mid_origin = self._get_airbase_single(province=o_province, postal_code=o_postal_code)
            mid_destination = self.get_single_base(airport_code=self._winnipeg_airport)
        elif d_province.upper() not in ["NT", "NU", "MB"]:
            mid_origin = self._get_airbase_single(province=o_province, postal_code=o_postal_code)
            mid_destination = self.get_single_base(airport_code=self._winnipeg_airport)
        elif d_province.upper() == "MB" and o_province.upper() not in ["NT", "NU", "MB"]:
            mid_origin = self.get_single_base(airport_code=self._winnipeg_airport)
            mid_destination = self._get_airbase_single(province=d_province, postal_code=d_postal_code)
        else:
            mid_origin = self._get_airbase_single(province=o_province, postal_code=o_postal_code)
            mid_destination = self._get_airbase_single(province=d_province, postal_code=d_postal_code)

        return mid_origin, mid_destination
