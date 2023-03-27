from django.core.exceptions import ObjectDoesNotExist
from django.db import connection

from api.globals.carriers import CAN_NORTH
from api.models import Airbase


class CanadianNorthAirbase:
    # NT
    _norman_wells = "X0E0V0"
    _yellowknife = "X1A"
    _yellowknife_full = "X1A2R3"
    _inuvik = "X0E0T0"
    _hay_river = "X0E0R9"
    _fort_simpson = "X0E0N0"

    _tuktoyaktuk = "X0E1C0"
    _tsiigehtchic = "X0E0B0"

    # Interline - NT
    _aklavik = "X0E0A0"
    _fort_good_hope = "X0E0H0"
    _colville_lake = "X0E1L0"
    _tulita = "X0E0K0"
    _deline = "X0E0G0"
    _f_mcpherson = "X0E0J0"
    _paulatuk = "X0E1N0"
    _sachs_harbour = "X0E0Z0"
    _ulukhaktok = "X0E0S0"
    _fort_smith = "X0E0P0"

    # NU
    _cape_dorset = "X0A0C0"
    _cambridge_bay = "X0B0C0"
    _hall_beach = "X0A0K0"
    _igloolik = "X0A0L0"
    _iqaluit = "X0A0H0"
    _gjoa_haven = "X0B1J0"
    _kugaaruk = "X0B1K0"
    _kugluktuk = "X0B0E0"
    _pangnirtung = "X0A0R0"
    _pond_inlet = "X0A0S0"
    _qikiqtarjuaq = "X0A0B0"
    _rankin_inlet = "X0C0G0"
    _taloyoak = "X0B1B0"
    _arctic_bay = "X0A0A0"
    _clyde_river = "X0A0E0"
    _kimmirut = "X0A0N0"
    _resolute_bay = "X0A0V0"
    _grise_fiord = "X0A0J0"

    # Interline - NU
    _sanikiluaq = "X0A0W0"

    # Northern Quebec
    _kuujjuaq = "J0M1C0"

    # Interline - Northern Quebec
    _kangiqsualujjuaq = "J0M1N0"
    _aupaluk = "J0M1X0"
    _tasiujaq = "J0M1T0"
    _kangirsuk = "J0M1A0"
    _quaqtaq = "J0M1J0"
    _kangigsujuaq = "J0M1K0"
    _salluit = "J0M1S0"
    _ivujivik = "J0M1H0"
    _akulivik = "J0M1V0"
    _puvirnituq = "J0M1P0"
    _inukjuak = "J0M1M0"
    _umiujaq = "J0M1Y0"
    _kuujjuaraapik = "J0M0A6"
    _chisasibi = "J0M1E0"
    _schefferville = "G0G2T0"

    # South
    _montreal = "H9P2S7"
    _ottawa = "K1V0R1"
    _ottawa_two = "K1V0R4"
    _edmonton = "T9E0V6"

    _north = ["NT", "NU"]
    _quebec = "QC"

    def __init__(self):
        self._western_arctic = [
            self._norman_wells, self._yellowknife_full, self._inuvik, self._hay_river, self._fort_simpson,
            self._ulukhaktok, self._cambridge_bay, self._taloyoak, self._kugaaruk, self._kugluktuk, self._gjoa_haven,
            self._rankin_inlet, self._tsiigehtchic, self._f_mcpherson, self._tuktoyaktuk, self._aklavik,
            self._fort_good_hope, self._colville_lake, self._tulita, self._deline, self._paulatuk, self._sachs_harbour,
            self._ulukhaktok, self._fort_smith
        ]

        self._eastern_arctic = [
            self._cape_dorset, self._hall_beach, self._igloolik, self._iqaluit, self._pangnirtung, self._pond_inlet,
            self._qikiqtarjuaq, self._arctic_bay, self._clyde_river, self._kimmirut, self._resolute_bay,
            self._grise_fiord, self._sanikiluaq
        ]

        self._north_quebec = [
            self._kuujjuaq, self._kangiqsualujjuaq, self._aupaluk, self._tasiujaq, self._kangirsuk, self._quaqtaq,
            self._kangigsujuaq, self._salluit, self._ivujivik, self._akulivik, self._puvirnituq, self._inukjuak,
            self._umiujaq, self._kuujjuaraapik, self._chisasibi, self._schefferville
        ]

    @staticmethod
    def _get_airbase_data(postal_code: str) -> dict:
        try:
            airbase = Airbase.objects.select_related("address__province__country").get(carrier__code=CAN_NORTH, address__postal_code=postal_code)
        except ObjectDoesNotExist as e:
            connection.close()
            return {}
        return airbase.get_ship_dict

    @staticmethod
    def get_single_base(airport_code: str) -> dict:

        try:
            airbase = Airbase.objects.select_related("address__province__country").get(carrier__code=CAN_NORTH, code=airport_code)

            return airbase.get_ship_dict
        except ObjectDoesNotExist as e:
            connection.close()
            return {}

    def _northwest_territories(self, postal_code: str) -> dict:

        if postal_code.startswith(self._yellowknife):
            return self._get_airbase_data(postal_code=self._yellowknife_full)
        elif postal_code == self._norman_wells:
            return self._get_airbase_data(postal_code=self._norman_wells)
        elif postal_code == self._inuvik:
            return self._get_airbase_data(postal_code=self._inuvik)
        elif postal_code in [
            "X0E0R9", "X0E0R5", "X0E0R0", "X0E0R2", "X0E0R3", "X0E0R4", "X0E0R6", "X0E0R7", "X0E0R8", "X0E0R9",
            'X0E1G1', "X0E1G2", "X0E1G3", "X0E1G4", "X0E1G5"
        ]:
            return self._get_airbase_data(postal_code=self._hay_river)
        elif postal_code == self._fort_simpson:
            return self._get_airbase_data(postal_code=self._fort_simpson)
        elif postal_code == self._ulukhaktok:
            return self._get_airbase_data(postal_code=self._ulukhaktok)
        elif postal_code == self._tuktoyaktuk:
            return self._get_airbase_data(postal_code=self._inuvik)
        elif postal_code == self._f_mcpherson:
            return self._get_airbase_data(postal_code=self._inuvik)
        elif postal_code == self._tsiigehtchic:
            return self._get_airbase_data(postal_code=self._inuvik)
        elif postal_code == self._aklavik:
            return self._get_airbase_data(postal_code=self._aklavik)
        elif postal_code == self._fort_good_hope:
            return self._get_airbase_data(postal_code=self._fort_good_hope)
        elif postal_code == self._colville_lake:
            return self._get_airbase_data(postal_code=self._colville_lake)
        elif postal_code == self._tulita:
            return self._get_airbase_data(postal_code=self._tulita)
        elif postal_code == self._deline:
            return self._get_airbase_data(postal_code=self._deline)
        elif postal_code == self._paulatuk:
            return self._get_airbase_data(postal_code=self._paulatuk)
        elif postal_code == self._sachs_harbour:
            return self._get_airbase_data(postal_code=self._sachs_harbour)
        elif postal_code == self._fort_smith:
            return self._get_airbase_data(postal_code=self._fort_smith)

        return {}

    def _nunavut(self, postal_code: str) -> dict:

        if postal_code == self._cape_dorset:
            return self._get_airbase_data(postal_code=self._cape_dorset)
        elif postal_code == self._cambridge_bay:
            return self._get_airbase_data(postal_code=self._cambridge_bay)
        elif postal_code == self._hall_beach:
            return self._get_airbase_data(postal_code=self._hall_beach)
        elif postal_code == self._igloolik:
            return self._get_airbase_data(postal_code=self._igloolik)
        elif postal_code == self._iqaluit:
            return self._get_airbase_data(postal_code=self._iqaluit)
        elif postal_code == self._kugaaruk:
            return self._get_airbase_data(postal_code=self._kugaaruk)
        elif postal_code == self._kugluktuk:
            return self._get_airbase_data(postal_code=self._kugluktuk)
        elif postal_code == self._pangnirtung:
            return self._get_airbase_data(postal_code=self._pangnirtung)
        elif postal_code == self._pond_inlet:
            return self._get_airbase_data(postal_code=self._pond_inlet)
        elif postal_code == self._qikiqtarjuaq:
            return self._get_airbase_data(postal_code=self._qikiqtarjuaq)
        elif postal_code == self._rankin_inlet:
            return self._get_airbase_data(postal_code=self._rankin_inlet)
        elif postal_code == self._taloyoak:
            return self._get_airbase_data(postal_code=self._taloyoak)
        elif postal_code == self._gjoa_haven:
            return self._get_airbase_data(postal_code=self._gjoa_haven)
        elif postal_code == self._arctic_bay:
            return self._get_airbase_data(postal_code=self._arctic_bay)
        elif postal_code == self._clyde_river:
            return self._get_airbase_data(postal_code=self._clyde_river)
        elif postal_code == self._kimmirut:
            return self._get_airbase_data(postal_code=self._kimmirut)
        elif postal_code == self._resolute_bay:
            return self._get_airbase_data(postal_code=self._resolute_bay)
        elif postal_code == self._grise_fiord:
            return self._get_airbase_data(postal_code=self._grise_fiord)
        elif postal_code == self._sanikiluaq:
            return self._get_airbase_data(postal_code=self._sanikiluaq)

        return {}

    def _northern_quebec(self, postal_code: str) -> dict:

        if postal_code == self._kuujjuaq:
            return self._get_airbase_data(postal_code=self._kuujjuaq)
        elif postal_code == self._kangiqsualujjuaq:
            return self._get_airbase_data(postal_code=self._kangiqsualujjuaq)
        elif postal_code == self._aupaluk:
            return self._get_airbase_data(postal_code=self._aupaluk)
        elif postal_code == self._tasiujaq:
            return self._get_airbase_data(postal_code=self._tasiujaq)
        elif postal_code == self._kangirsuk:
            return self._get_airbase_data(postal_code=self._kangirsuk)
        elif postal_code == self._quaqtaq:
            return self._get_airbase_data(postal_code=self._quaqtaq)
        elif postal_code == self._kangigsujuaq:
            return self._get_airbase_data(postal_code=self._kangigsujuaq)
        elif postal_code == self._salluit:
            return self._get_airbase_data(postal_code=self._salluit)
        elif postal_code == self._ivujivik:
            return self._get_airbase_data(postal_code=self._ivujivik)
        elif postal_code == self._akulivik:
            return self._get_airbase_data(postal_code=self._akulivik)
        elif postal_code == self._puvirnituq:
            return self._get_airbase_data(postal_code=self._puvirnituq)
        elif postal_code == self._inukjuak:
            return self._get_airbase_data(postal_code=self._inukjuak)
        elif postal_code == self._umiujaq:
            return self._get_airbase_data(postal_code=self._umiujaq)
        elif postal_code == self._kuujjuaraapik:
            return self._get_airbase_data(postal_code=self._kuujjuaraapik)
        elif postal_code == self._chisasibi:
            return self._get_airbase_data(postal_code=self._chisasibi)
        elif postal_code == self._schefferville:
            return self._get_airbase_data(postal_code=self._schefferville)

        return {}

    def _alberta(self) -> dict:
        return self._get_airbase_data(postal_code=self._edmonton)

    def _ontario(self, is_northbound: bool = True) -> dict:

        if is_northbound:
            return self._get_airbase_data(postal_code=self._ottawa)
        else:
            data = self._get_airbase_data(postal_code=self._ottawa_two)
            data["base"] = "YOW"
            return data

    def get_yellowknife(self) -> dict:
        return self._get_airbase_data(postal_code=self._yellowknife_full)

    def get_edmonton(self) -> dict:
        return self._get_airbase_data(postal_code=self._edmonton)

    def get_ottawa(self) -> dict:
        return self._get_airbase_data(postal_code=self._ottawa)

    def _get_north(self, province: str, postal_code: str):
        if province == "NT":
            return self._northwest_territories(postal_code=postal_code)
        elif province == "NU":
            return self._nunavut(postal_code=postal_code)
        elif province == "QC":
            return self._northern_quebec(postal_code=postal_code)

        return {}

    def _get_south(self, province: str):
        if province == "AB":
            return self._alberta()
        elif province == "ON":
            return self._ontario()

        return {}

    def get_airbase(self, o_province: str, o_postal_code: str, d_province: str, d_postal_code: str) -> tuple:
        """
            Determine the airbases for a canadian north shipment
            :param o_province: Origin Province: IE: AB, NT
            :param o_postal_code: Canadian Postal Code
            :param d_province: Destination Province: IE: AB, NT
            :param d_postal_code: Canadian Postal Code
            :return: tuple of Dictionaries of Airbases for Origin and Destination
        """
        mid_origin = {}
        mid_destination = {}

        if (o_province in self._north and d_province in self._north) or (o_postal_code in self._north_quebec and d_postal_code in self._north_quebec) or (o_province in self._north and d_postal_code in self._north_quebec) or (o_postal_code in self._north_quebec and d_province in self._north):

            # north to north
            mid_origin = self._get_north(province=o_province, postal_code=o_postal_code)
            mid_destination = self._get_north(province=d_province, postal_code=d_postal_code)

        elif (o_postal_code in self._north_quebec and d_province not in self._north and d_postal_code not in self._north_quebec) or (o_province in self._north and d_province not in self._north and d_postal_code not in self._north_quebec):

            # north to south
            mid_origin = self._get_north(province=o_province, postal_code=o_postal_code)

            # Determine which southern airbase to use YEG or YOW
            if o_postal_code in self._eastern_arctic or o_postal_code in self._north_quebec:
                mid_destination = self._ontario(is_northbound=False)
            else:
                mid_destination = self._alberta()

        elif o_province not in self._north and (d_province in self._north or d_postal_code in self._north_quebec):

            # south to north
            # Determine which southern airbase to use YEG or YOW
            if d_postal_code in self._eastern_arctic or d_postal_code in self._north_quebec:
                mid_origin = self._ontario()
            else:
                mid_origin = self._alberta()

            mid_destination = self._get_north(province=d_province, postal_code=d_postal_code)

        return mid_origin, mid_destination
