from django.core.exceptions import ObjectDoesNotExist
from django.db import connection

from api.globals.carriers import WESTJET
from api.models import Airbase


class WestJetAirbase:
    # AB
    _edmonton = "YEG"
    _calgary = "YYC"
    _mcmurray = "YMM"
    _grande_prairie = "YQU"

    # BC
    _terrace = "YXT"
    _victoria = "YYJ"
    _vancouver = "YVR"
    _prince_george = "YXS"
    _kelowna = "YLW"
    _comox = "YQQ"

    # MB
    _winnipeg = "YWG"

    # NB
    _moncton = "YQM"

    # NL
    _st_john = "YYT"

    # NT
    _yellowknife = "YZF"

    # NS
    _halifax = "YHZ"

    # ON
    _ottawa = "YOW"
    _thunder_bay = "YQT"
    _toronto = "YYZ"

    # PEI
    _charlottetown = "YYG"

    # QC
    _montreal = "YUL"

    # SK
    _regina = "YQR"
    _saskatoon = "YXE"

    @staticmethod
    def _get_airbase_data(airport_code: str) -> dict:
        try:
            airbase = Airbase.objects.get(carrier__code=WESTJET, code=airport_code)
        except ObjectDoesNotExist as e:
            return {}
        return airbase.get_ship_dict

    def _alberta(self, postal_code: str) -> dict:
        if postal_code in ["T0E", "T7V", "T7E", "T7S", "T8N", "T7Z", "T7A", "T9S", "T7N", "T7P", "T8R", "T9A", "T4J",
                           "T9E", "T4L", "T9W", "T4V", "T4X", "T0B", "T9X", "T9C", "T8L", "T9N", "T9M", "T0A", "T5A",
                           "T5B", "T5C", "T5E", "T5G", "T5H", "T5J", "T5K", "T5L", "T5M", "T5N", "T5P", "T5R", "T5S",
                           "T5T", "T5V", "T5W", "T5X", "T5Y", "T5Z", "T6A", "T6B", "T6C", "T6E", "T6G", "T6H", "T6J",
                           "T6K", "T6L", "T6M", "T6N", "T6P", "T6R", "T6S", "T6T", "T6V", "T6W", "T6X", "T7X", "T7Y",
                           "T8A", "T8B", "T8C", "T8E", "T8G", "T8H", "T8T", "T9V", "T9S", "T9W", "T0T", "T0V", "T0N",
                           "T4T", "T6Y", "T9G"]:
            # Edmonton
            return self._get_airbase_data(airport_code=self._edmonton)
        elif postal_code in ["T4S", "T0M", "T4H", "T4G", "T1W", "T0C", "T0J", "T1V", "T0L", "T1R", "T1P", "T1G", "T1Z",
                             "T1M", "T0K", "T1Y", "T1A", "T1B", "T1C", "T1H", "T1J", "T1K", "T1L", "T1S", "T1X", "T1Y",
                             "T2A", "T2B", "T2C", "T2E", "T2G", "T2H", "T2J", "T2K", "T2L", "T2M", "T2N", "T2P", "T2P",
                             "T2R", "T2S", "T2T", "T2V", "T2W", "T2X", "T2Y", "T2Z", "T3A", "T3B", "T3C", "T3E", "T3G",
                             "T3H", "T3J", "T3K", "T3L", "T3M", "T3N", "T3P", "T3R", "T3S", "T3Z", "T4A", "T4B", "T4E",
                             "T4N", "T4P", "T4R", "T3T", "T4C"]:
            # Calgary
            return self._get_airbase_data(airport_code=self._calgary)
        elif postal_code in ["T0H", "T8S", "T0G", "T8V", "T8W", "T8X"]:
            # Grande Prairie
            return self._get_airbase_data(airport_code=self._grande_prairie)
        elif postal_code in ["T0P", "T9J", "T9K", "T9H"]:
            # Fort Mac
            return self._get_airbase_data(airport_code=self._mcmurray)

        return self._get_airbase_data(airport_code=self._edmonton)

    def _british_columbia(self, postal_code: str) -> dict:

        if postal_code in ["V0N", "V8A", "V0P", "V0K", "V0N", "V1K", "V9K", "V0M", "V0X", "V2A", "V7N", "V7P", "V7R",
                           "V7S", "V7T", "V7V", "V7W", "V7X", "V7Y", "V8B", "V7A", "V7B", "V7C", "V7E", "V7G", "V7H",
                           "V7J", "V7K", "V7L", "V7M", "V6A", "V6B", "V6C", "V6E", "V6G", "V6H", "V6K", "V6K", "V6L",
                           "V6M", "V6N", "V6P", "V6R", "V6S", "V6T", "V6V", "V6W", "V6Y", "V6Z", "V5H", "V5J", "V5K",
                           "T5L", "V5M", "V5N", "V5P", "V5R", "V5S", "V5T", "V5V", "V5W", "V5X", "V5Y", "V5Z", "V5A",
                           "T5B", "V5C", "V5G", "V5E", "V4Z", "V4X", "V4W", "V4A", "V4B", "V4C", "V4E", "V4G", "V4K",
                           "T4L", "V4M", "V4N", "V4P", "V4R", "V4S", "V2P", "V2R", "V2S", "V2T", "V2V", "V2W", "V2X",
                           "V2Y", "V2Z", "V3A", "V3B", "V3C", "V3E", "V3G", "V3H", "V3J", "V3K", "V3L", "V3M", "V3N",
                           "V3N", "V3R", "V3S", "V3T", "V3V", "V3W", "V3X", "V3Y", "V1M"]:
            # Vancouver
            return self._get_airbase_data(airport_code=self._vancouver)
        elif postal_code in ["V0E", "V1E", "V0A", "V0B", "V4V", "V0H", "V1R", "V1N", "V1L", "V0B", "V1A", "V1C", "V4T",
                             "V1B", "V1H", "V1P", "V1S", "V1T", "V1V", "V1W", "V1X", "V1Y", "V1Z", "V2B", "V2C", "V2E",
                             "V2H"]:
            # Kelowna
            return self._get_airbase_data(airport_code=self._kelowna)
        elif postal_code in ["V9Y", "V9P", "V9G", "V9L", "V8K", "V0S", "V8L", "V8M", "V8N", "V8P", "V8R", "V8S", "V8T",
                             "T8V", "V8W", "V8X", "V8Y", "V8Z", "V9A", "V9B", "V9C", "V9E", "V9R", "V9S", "V9T", "V9V",
                             "T9X", "V9Z"]:
            # Victoria
            return self._get_airbase_data(airport_code=self._victoria)
        elif postal_code in ["V0N", "V0P", "V9J", "V0R", "V9H", "V9M", "V9N", "V9W"]:
            # Comox
            return self._get_airbase_data(airport_code=self._comox)
        elif postal_code in ["V0W", "V0T", "V0V", "V8J", "V8C", "V8G", "V0T"]:
            # Terrace
            return self._get_airbase_data(airport_code=self._terrace)
        elif postal_code in ["V0C", "V1J", "V1G", "V2J", "V0L", "V2G", "V0J", "V2K", "V2L", "V2M", "V2N"]:
            # Prince George
            return self._get_airbase_data(airport_code=self._prince_george)

        return self._get_airbase_data(airport_code=self._vancouver)

    def _manitoba(self) -> dict:
        return self._get_airbase_data(airport_code=self._winnipeg)

    def _new_brunswick(self) -> dict:
        return self._get_airbase_data(airport_code=self._moncton)

    def _newfoundland(self) -> dict:
        return self._get_airbase_data(airport_code=self._st_john)

    def _nova_scotia(self) -> dict:
        return self._get_airbase_data(airport_code=self._halifax)

    def _northwest_territories(self) -> dict:
        return self._get_airbase_data(airport_code=self._yellowknife)

    def _ontario(self, postal_code: str) -> dict:
        first_letter = postal_code[:1]

        if first_letter.upper() == "K" or postal_code in ["P1A", "P1B", "P1C", "P1H", "P1L", "P1P", "P2A", "P2B", "P2N",
                                                          "P3A", "P3A", "P3B", "P3C", "P3E", "P3G", "P3L", "P3N", "P3P",
                                                          "P3Y", "P0A", "P0B", "P0C", "P0E", "P0G", "P0H", "P0J", "P0K",
                                                          "P0M", "P0P", "P0R"]:
            # Ottawa
            return self._get_airbase_data(airport_code=self._ottawa)
        elif first_letter.upper() in ["L", "M", "N"]:
            # Toronto
            return self._get_airbase_data(airport_code=self._toronto)
        elif postal_code in ["P4N", "P4P", "P4R", "P5A", "P5E", "P5N", "P5A", "P6A", "P6B", "P6C", "P6", "P7A", "P7B",
                             "P7C", "P7E", "P7G", "P7J", "P7K", "P7L", "P7N", "P7T", "P9A", "P9N", "P0L", "P0N", "P0S",
                             "P0T", "P0V", "P0W", "P0X", "P0Y"]:
            # Thunder Bay
            return self._get_airbase_data(airport_code=self._thunder_bay)

        return self._get_airbase_data(airport_code=self._ottawa)

    def _pei(self) -> dict:
        return self._get_airbase_data(airport_code=self._charlottetown)

    def _quebec(self) -> dict:
        return self._get_airbase_data(airport_code=self._montreal)

    def _saskatchewan(self, postal_code: str) -> dict:
        if postal_code in ["S0M", "S0J", "S0P", "S0E", "S0K", "S9A", "S4L", "S4M", "S4N", "S4P", "S4R", "S4T", "S4V",
                           "S4W", "S4X", "S4Y", "S4Z", "S6V", "S6W", "S6X", "S7H", "S7J", "S7K", "S7L", "S7M", "S7N",
                           "S7P", "S7R", "S7S", "S7T", "S7V", "S7W", "S9V"]:
            # Saskatoon
            return self._get_airbase_data(airport_code=self._saskatoon)
        elif postal_code in ["S0L", "S9H", "S0N", "S0H", "S0G", "S0A", "S3N", "S2V", "S4H", "S4A", "S0C", "S4A", "S6H",
                             "S6J", "S6K", "S4S", "S4V"]:
            # Regina
            return self._get_airbase_data(airport_code=self._regina)

        return self._get_airbase_data(airport_code=self._saskatoon)

    def _get_airbase_single(self, province: str, postal_code: str) -> dict:
        postal_code = postal_code.replace(" ", "").upper()
        fsa = postal_code[:3]

        if province == "AB":
            return self._alberta(postal_code=fsa)
        elif province == "BC":
            return self._british_columbia(postal_code=fsa)
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
            pass
        elif province == "ON":
            return self._ontario(postal_code=fsa)
        elif province == "PE":
            return self._pei()
        elif province == "QC":
            return self._quebec()
        elif province == "SK":
            return self._saskatchewan(postal_code=fsa)
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
            airbase = Airbase.objects.get(carrier__code=WESTJET, code=airport_code)

            return airbase.get_ship_dict
        except ObjectDoesNotExist as e:
            connection.close()
            return {}
