from django.core.exceptions import ObjectDoesNotExist
from django.db import connection

from api.globals.carriers import CARGO_JET
from api.models import Airbase


class CargojetAirbase:
    # AB
    _edmonton = "YEG"
    _calgary = "YYC"

    # BC
    _vancouver = "YVR"

    # MB
    _winnipeg = "YWG"

    # NB
    _moncton = "YQM"

    # NL
    _st_john = "YYT"

    # NS
    _halifax = "YHZ"

    # QC
    _mirabel = "YMX"

    # ON
    _ottawa = "YOW"
    _hamilton = "YHM"
    _toronto = "YYZ"

    # SK
    _regina = "YQR"
    _saskatoon = "YXE"

    @staticmethod
    def _get_airbase_data(airport_code: str) -> dict:
        try:
            airbase = Airbase.objects.get(carrier__code=CARGO_JET, code=airport_code)
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
                           "T4T", "T6Y", "T9G", "T0H", "T8S", "T0G", "T8V", "T8W", "T8X", "T0P", "T9J", "T9K", "T9H"]:
            # Edmonton
            return self._get_airbase_data(airport_code=self._edmonton)
        elif postal_code in ["T4S", "T0M", "T4H", "T4G", "T1W", "T0C", "T0J", "T1V", "T0L", "T1R", "T1P", "T1G", "T1Z",
                             "T1M", "T0K", "T1Y", "T1A", "T1B", "T1C", "T1H", "T1J", "T1K", "T1L", "T1S", "T1X", "T1Y",
                             "T2A", "T2B", "T2C", "T2E", "T2G", "T2H", "T2J", "T2K", "T2L", "T2M", "T2N", "T2P",
                             "T2R", "T2S", "T2T", "T2V", "T2W", "T2X", "T2Y", "T2Z", "T3A", "T3B", "T3C", "T3E", "T3G",
                             "T3H", "T3J", "T3K", "T3L", "T3M", "T3N", "T3P", "T3R", "T3S", "T3Z", "T4A", "T4B", "T4E",
                             "T4N", "T4P", "T4R", "T3T", "T4C"]:
            # Calgary
            return self._get_airbase_data(airport_code=self._calgary)

        return self._get_airbase_data(airport_code=self._edmonton)

    def _british_columbia(self) -> dict:
        return self._get_airbase_data(airport_code=self._vancouver)

    def _manitoba(self) -> dict:
        return self._get_airbase_data(airport_code=self._winnipeg)

    def _new_brunswick(self) -> dict:
        return self._get_airbase_data(airport_code=self._moncton)

    def _newfoundland(self) -> dict:
        return self._get_airbase_data(airport_code=self._st_john)

    def _nova_scotia(self) -> dict:
        return self._get_airbase_data(airport_code=self._halifax)

    def _quebec(self) -> dict:
        return self._get_airbase_data(airport_code=self._mirabel)

    def _ontario(self, postal_code: str) -> dict:
        first_letter = postal_code[:1]

        if first_letter.upper() == "K" or postal_code in ["P1A", "P1B", "P1C", "P1H", "P1L", "P1P", "P2A", "P2B", "P2N",
                                                          "P3A", "P3A", "P3B", "P3C", "P3E", "P3G", "P3L", "P3N", "P3P",
                                                          "P3Y", "P0A", "P0B", "P0C", "P0E", "P0G", "P0H", "P0J", "P0K",
                                                          "P0M", "P0P", "P0R", "P4N", "P4P", "P4R", "P5A", "P5E", "P5N",
                                                          "P5A", "P6A", "P6B", "P6C", "P6", "P7A", "P7B", "P7C", "P7E",
                                                          "P7G", "P7J", "P7K", "P7L", "P7N", "P7T", "P9A", "P9N", "P0L",
                                                          "P0N", "P0S", "P0T", "P0V", "P0W", "P0X", "P0Y"]:
            # Ottawa
            return self._get_airbase_data(airport_code=self._ottawa)
        elif postal_code in ["L8P", "L0R", "L8E", "L8H", "L8J", "L8K", "L8L", "L8M", "L8N", "L8R", "L9C", "L8S", "L8T",
                             "L8V", "L8W", "L9A", "L9B", "L8G", "L7P", "L8B"]:
            # Hamilton
            return self._get_airbase_data(airport_code=self._hamilton)
        elif first_letter.upper() in ["L", "M", "N"]:
            # Toronto
            return self._get_airbase_data(airport_code=self._toronto)

        return self._get_airbase_data(airport_code=self._ottawa)

    def _saskatchewan(self, postal_code: str) -> dict:
        if postal_code in ["S0M", "S0J", "S0P", "S0E", "S0K", "S9A", "S4L", "S4M", "S4N", "S4P", "S4R", "S4T",
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
            pass
        elif province == "NU":
            pass
        elif province == "ON":
            return self._ontario(postal_code=fsa)
        elif province == "PE":
            pass
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
            airbase = Airbase.objects.get(carrier__code=CARGO_JET, code=airport_code)

            return airbase.get_ship_dict
        except ObjectDoesNotExist as e:
            connection.close()
            return {}
