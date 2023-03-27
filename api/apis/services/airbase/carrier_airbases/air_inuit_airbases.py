from django.core.exceptions import ObjectDoesNotExist

from api.globals.carriers import AIR_INUIT
from api.models import Airbase


class AirInuitAirbase:

    # NU
    _sanikiluaq = "YSK"
    _sanikiluaq_postal = "X0A0W0"

    # QC
    _akulivik = "AKV"
    _akulivik_postal = "J0M1V0"
    _aupaluk = "YPJ"
    _aupaluk_postal = "J0M1X0"
    _inukjuak = "YPH"
    _inukjuak_postal = "J0M1M0"
    _ivujivik = "YIK"
    _ivujivik_postal = "J0M1H0"
    _kangiqsualujjuaq = "XGR"
    _kangiqsualujjuaq_postal = "J0M1N0"
    _kangigsujuaq = "YWB"
    _kangigsujuaq_postal = "J0M1K0"
    _kangirsuk = "YKG"
    _kangirsuk_postal = "J0M1A0"
    _kuujjuaaq = "YVP"
    _kuujjuaaq_postal = "J0M1C0"
    _kuujjuaraapik = "YGW"
    _kuujjuaraapik_postal = "J0M0A6"
    _la_grande_chisasibi = "YGL"
    _la_grande_chisasibi_postal = "J0M1E0"
    _puvirnituq = "YPX"
    _puvirnituq_postal = "J0M1P0"
    _quaqtaq = "YQC"
    _quaqtaq_postal = "J0M1J0"
    _quebec_city = "YQB"
    _quebec_city_postal = "G2G2T2"
    _salluit = "YZG"
    _salluit_postal = "J0M1S0"
    _schefferville = "YKL"
    _schefferville_postal = "G0G2T0"
    _septlles = "YZV"
    _tasiujaq = "YTQ"
    _tasiujaq_postal = "J0M1T0"
    _umiujaq = "YUD"
    _umiujaq_postal = "J0M1Y0"
    _wabush = "YWK"
    _wabush_postal = "A0R1B0"

    _montreal = "YUL"

    @staticmethod
    def _get_airbase_data(airport_code: str) -> dict:
        try:
            airbase = Airbase.objects.get(carrier__code=AIR_INUIT, code=airport_code)
        except ObjectDoesNotExist as e:
            return {}
        return airbase.get_ship_dict

    def _alberta(self) -> dict:
        """
        Get AB airbase location for air inuit, in this case montreal
        """

        return self._get_airbase_data(airport_code=self._montreal)

    def _british_columbia(self) -> dict:
        """
        Get BC airbase location for air inuit, in this case montreal
        """
        return self._get_airbase_data(airport_code=self._montreal)

    def _manitoba(self) -> dict:
        """
        Get MB airbase location for air inuit, in this case montreal
        """
        return self._get_airbase_data(airport_code=self._montreal)

    def _new_brunswick(self) -> dict:
        """
            Get NB airbase location for air inuit, in this case montreal
        """
        return self._get_airbase_data(airport_code=self._montreal)

    def _newfoundland(self) -> dict:
        """
            Get NL airbase location for air inuit, in this case montreal
        """
        return self._get_airbase_data(airport_code=self._montreal)

    def _nova_scotia(self) -> dict:
        """
            Get NS airbase location for air inuit, in this case montreal
        """
        return self._get_airbase_data(airport_code=self._montreal)

    def _northwest_territories(self) -> dict:
        """
            Get NT airbase location for air inuit, in this case montreal
        """
        return self._get_airbase_data(airport_code=self._montreal)

    def _nunavut(self, postal_code: str) -> dict:
        """
            Get NU airbase location for air inuit
        """

        if postal_code == self._sanikiluaq_postal:
            return self._get_airbase_data(airport_code=self._sanikiluaq)

        return {}

    def _ontario(self) -> dict:
        """
            Get ON airbase location for air inuit, in this case montreal
        """
        return self._get_airbase_data(airport_code=self._montreal)

    def _pei(self) -> dict:
        """
            Get PE airbase location for air inuit, in this case montreal
        """
        return self._get_airbase_data(airport_code=self._montreal)

    def _quebec(self, postal_code: str) -> dict:
        """
            Get QC airbase location for air inuit
        """
        fsa = postal_code[:3]

        if postal_code == self._akulivik_postal:
            return self._get_airbase_data(airport_code=self._akulivik)
        elif postal_code == self._aupaluk_postal:
            return self._get_airbase_data(airport_code=self._aupaluk)
        elif postal_code == self._inukjuak_postal:
            return self._get_airbase_data(airport_code=self._inukjuak)
        elif postal_code == self._ivujivik_postal:
            return self._get_airbase_data(airport_code=self._ivujivik)
        elif postal_code == self._kangiqsualujjuaq_postal:
            return self._get_airbase_data(airport_code=self._kangiqsualujjuaq)
        elif postal_code == self._kangigsujuaq_postal:
            return self._get_airbase_data(airport_code=self._kangigsujuaq)
        elif postal_code == self._kangirsuk_postal:
            return self._get_airbase_data(airport_code=self._kangirsuk)
        elif postal_code == self._kuujjuaaq_postal:
            return self._get_airbase_data(airport_code=self._kuujjuaaq)
        elif postal_code in [self._kuujjuaraapik_postal, "J0M1G0"]:
            return self._get_airbase_data(airport_code=self._kuujjuaraapik)
        elif postal_code in ["J0Y2X0", "J0M1E0"]:
            return self._get_airbase_data(airport_code=self._la_grande_chisasibi)
        elif postal_code == self._puvirnituq_postal:
            return self._get_airbase_data(airport_code=self._puvirnituq)
        elif postal_code == self._quaqtaq_postal:
            return self._get_airbase_data(airport_code=self._quaqtaq)
        elif fsa in [
            "G1A", "G1B", "G1C", "G1E", "G1G", "G1H", "G1J", "G1K", "G1L", "G1M", "G1N", "G1P", "G1R", "G1S", "G1T",
            "G1V", "G1W", "G1X", "G1Y", "G2A", "G2B", "G2C", "G2E", "G2G", "G2J", "G2K", "G2L", "G2M", "G2N", "G3E",
            "G3G", "G3J", "G3K", "G3B", "G0A", "G3C", "G3L", "G3N", "G3H", "G3A", "G6V", "G6Y", "G6C", "G6W", "G6X",
            "G7A", "G6J", "G6Z", "G5V", "G0R", "G6E", "G0S"
        ]:
            return self._get_airbase_data(airport_code=self._quebec_city)
        elif postal_code == self._salluit_postal:
            return self._get_airbase_data(airport_code=self._salluit)
        elif postal_code in [self._schefferville_postal, "G0G0C6"]:
            return self._get_airbase_data(airport_code=self._schefferville)
        elif fsa in [
            "G4R", "G4S", "G4Z", "G0T"
        ]:
            return self._get_airbase_data(airport_code=self._septlles)
        elif postal_code == self._tasiujaq_postal:
            return self._get_airbase_data(airport_code=self._tasiujaq)
        elif postal_code == self._umiujaq_postal:
            return self._get_airbase_data(airport_code=self._umiujaq)
        elif postal_code == self._wabush_postal:
            return self._get_airbase_data(airport_code=self._wabush)

        return self._get_airbase_data(airport_code=self._montreal)

    def _saskatchewan(self) -> dict:
        """
            Get SK airbase location for air inuit, in this case montreal
        """
        return self._get_airbase_data(airport_code=self._montreal)

    def _get_airbase_single(self, province: str, postal_code: str) -> dict:
        postal_code = postal_code.replace(" ", "").upper()

        if province == "AB":
            return self._alberta()
        elif province == "BC":
            return self._british_columbia()
        elif province == "MB":
            return self._manitoba()
        elif province == "NB":
            return self._new_brunswick()
        elif province == "NL":
            return self._newfoundland()
        elif province == "NS":
            return self._nova_scotia()
        elif province == "NT":
            return self._northwest_territories()
        elif province == "NU":
            return self._nunavut(postal_code=postal_code)
        elif province == "ON":
            return self._ontario()
        elif province == "PE":
            return self._pei()
        elif province == "QC":
            return self._quebec(postal_code=postal_code)
        elif province == "SK":
            return self._saskatchewan()
        elif province == "YT":
            pass

        return {}

    def get_airbase(self, o_province: str, o_postal_code: str, d_province: str, d_postal_code: str) -> tuple:

        mid_origin = self._get_airbase_single(province=o_province, postal_code=o_postal_code)
        mid_destination = self._get_airbase_single(province=d_province, postal_code=d_postal_code)

        return mid_origin, mid_destination

    @staticmethod
    def get_single_base(airport_code: str) -> dict:

        try:
            airbase = Airbase.objects.get(carrier__code=AIR_INUIT, code=airport_code)

            return airbase.get_ship_dict
        except ObjectDoesNotExist as e:
            return {}
