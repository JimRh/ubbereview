from django.core.exceptions import ObjectDoesNotExist
from django.db import connection

from api.globals.carriers import AIR_NORTH
from api.models import Airbase


class AirNorthAirbase:

    # NT
    _yellowknife = "YZF"
    _inuvik = "YEV"

    __pc_inuvik = "X0E0T0"

    # YT
    _whitehorse = "YXY"
    _dawson_city = "YDA"
    _mayo = "YMA"
    _old_crow = "YOC"

    _pc_whitehorse = "Y1A0M7"
    _pc_dawson_city = "Y0B1G0"
    _pc_mayo = "YOB1M0"
    _pc_old_crow = "Y0B1N0"

    # AB
    _edmonton = "YEG"
    _calgary = "YYC"

    # BC
    _victoria = "YYJ"
    _vancouver = "YVR"
    _kelowna = "YLW"

    _north = ["NT", "YT"]

    @staticmethod
    def _get_airbase_data(airport_code: str) -> dict:
        try:
            airbase = Airbase.objects.get(carrier__code=AIR_NORTH, code=airport_code)
        except ObjectDoesNotExist as e:
            return {}
        return airbase.get_ship_dict

    #

    def _alberta(self, postal_code: str) -> dict:
        """
            Alberta Postal Codes for airbases choosing.

            Not Assigned:
                - T9Z, T8Z, T6Z, T4Z, T9Y, T8Y, T4Y T3Y, T3X, T7W, T4W, T3W, T3V, T9T, T7T, T1T, T9R, T7R, T9P, T8P,
                T1N, T8M, T7M, T9L, T7L, T8K, T7K, T4K, T8J, T7J, T7H, T7G, T1E, T7C, T9B, T7B

            :param postal_code: First three characters of the postal code.
            :return:
        """

        if postal_code in [
            "T0E", "T7V", "T7E", "T7S", "T8N", "T7Z", "T7A", "T9S", "T7N", "T7P", "T8R", "T9A", "T4J", "T9E", "T4L",
            "T9W", "T4V", "T4X", "T0B", "T9X", "T9C", "T8L", "T9N", "T9M", "T0A", "T5A", "T5B", "T5C", "T5E", "T5G",
            "T5H", "T5J", "T5K", "T5L", "T5M", "T5N", "T5P", "T5R", "T5S", "T5T", "T5V", "T5W", "T5X", "T5Y", "T5Z",
            "T6A", "T6B", "T6C", "T6E", "T6G", "T6H", "T6J", "T6K", "T6L", "T6M", "T6N", "T6P", "T6R", "T6S", "T6T",
            "T6V", "T6W", "T6X", "T7X", "T7Y", "T8A", "T8B", "T8C", "T8E", "T8G", "T8H", "T8T", "T9V", "T0V",
            "T0N", "T4T", "T0H", "T8S", "T0G", "T8V", "T8W", "T8X", "T0P", "T9J", "T9K", "T9H", "T6Y", "T9G"
        ]:
            # Edmonton
            return self._get_airbase_data(airport_code=self._edmonton)
        elif postal_code in [
            "T4S", "T0M", "T4H", "T4G", "T1W", "T0C", "T0J", "T1V", "T0L", "T1R", "T1P", "T1G", "T1Z", "T1M", "T0K",
            "T1Y", "T1A", "T1B", "T1C", "T1H", "T1J", "T1K", "T1L", "T1S", "T1X", "T1Y", "T2A", "T2B", "T2C", "T2E",
            "T2G", "T2H", "T2J", "T2K", "T2L", "T2M", "T2N", "T2P", "T2P", "T2R", "T2S", "T2T", "T2V", "T2W", "T2X",
            "T2Y", "T2Z", "T3A", "T3B", "T3C", "T3E", "T3G", "T3H", "T3J", "T3K", "T3L", "T3M", "T3N", "T3P", "T3R",
            "T3S", "T3Z", "T4A", "T4B", "T4E", "T4N", "T4P", "T4R", "T3T", "T4C", "T4M"
        ]:
            # Calgary
            return self._get_airbase_data(airport_code=self._calgary)

        # Default Calgary
        return self._get_airbase_data(airport_code=self._calgary)

    def _british_columbia(self, postal_code: str) -> dict:
        """
            BC Postal Codes for airbases choosing.

            Not Assigned:
                -

            :param postal_code: First three characters of the postal code.
            :return:
        """

        if postal_code in [
            "V0N", "V8A", "V0P", "V0K", "V0N", "V1K", "V9K", "V0M", "V0X", "V2A", "V7N", "V7P", "V7R", "V7S", "V7T",
            "V7V", "V7W", "V7X", "V7Y", "V8B", "V7A", "V7B", "V7C", "V7E", "V7G", "V7H", "V7J", "V7K", "V7L", "V7M",
            "V6A", "V6B", "V6C", "V6E", "V6G", "V6H", "V6K", "V6K", "V6L", "V6M", "V6N", "V6P", "V6R", "V6S", "V6T",
            "V6V", "V6W", "V6Y", "V6Z", "V5H", "V5J", "V5K", "T5L", "V5M", "V5N", "V5P", "V5R", "V5S", "V5T", "V5V",
            "V5W", "V5X", "V5Y", "V5Z", "V5A", "T5B", "V5C", "V5G", "V5E", "V4Z", "V4X", "V4W", "V4A", "V4B", "V4C",
            "V4E", "V4G", "V4K", "T4L", "V4M", "V4N", "V4P", "V4R", "V4S", "V2P", "V2R", "V2S", "V2T", "V2V", "V2W",
            "V2X", "V2Y", "V2Z", "V3A", "V3B", "V3C", "V3E", "V3G", "V3H", "V3J", "V3K", "V3L", "V3M", "V3N", "V3N",
            "V3R", "V3S", "V3T", "V3V", "V3W", "V3X", "V3Y", "V1M", "V0C", "V1J", "V1G", "V2J", "V0L", "V2G", "V0J",
            "V2K", "V2L", "V2M", "V2N", "V0W", "V0T", "V0V", "V8J", "V8C", "V8G", "V0T"
        ]:
            # Vancouver
            return self._get_airbase_data(airport_code=self._vancouver)
        elif postal_code in [
            "V0E", "V1E", "V0A", "V0B", "V4V", "V0H", "V1R", "V1N", "V1L", "V0B", "V1A", "V1C", "V4T", "V1B", "V1H",
            "V1P", "V1S", "V1T", "V1V", "V1W", "V1X", "V1Y", "V1Z", "V2B", "V2C", "V2E", "V2H"
        ]:
            # Kelowna
            return self._get_airbase_data(airport_code=self._kelowna)
        elif postal_code in [
            "V9Y", "V9P", "V9G", "V9L", "V8K", "V0S", "V8L", "V8M", "V8N", "V8P", "V8R", "V8S", "V8T", "T8V", "V8W",
            "V8X", "V8Y", "V8Z", "V9A", "V9B", "V9C", "V9E", "V9R", "V9S", "V9T", "V9V", "T9X", "V9Z", "V0N", "V0P",
            "V9J", "V0R", "V9H", "V9M", "V9N", "V9W"
        ]:
            # Victoria
            return self._get_airbase_data(airport_code=self._victoria)

        # Default Vancouver
        return self._get_airbase_data(airport_code=self._vancouver)

    def _northwest_territories(self) -> dict:
        return self._get_airbase_data(airport_code=self._inuvik)

    def _yukon(self, postal_code: str) -> dict:
        fsa = postal_code[:3]

        if fsa in ["Y1A"]:
            # Whitehorse
            return self._get_airbase_data(airport_code=self._whitehorse)
        elif postal_code == self._pc_dawson_city:
            # Dawson City
            return self._get_airbase_data(airport_code=self._dawson_city)
        elif postal_code in ["YOB1M0", "Y0B1M1"]:
            # Mayo
            return self._get_airbase_data(airport_code=self._mayo)
        elif postal_code == self._pc_old_crow:
            # Old Crow
            return self._get_airbase_data(airport_code=self._old_crow)

        # Default Whitehorse
        return self._get_airbase_data(airport_code=self._whitehorse)

    def _get_airbase_single(self, province: str, postal_code: str) -> dict:
        postal_code = postal_code.replace(" ", "").upper()
        fsa = postal_code[:3]

        if province == "AB":
            return self._alberta(postal_code=fsa)
        elif province == "BC":
            return self._british_columbia(postal_code=fsa)
        elif province == "MB":
            return self._get_airbase_data(airport_code=self._vancouver)
        elif province == "NB":
            return self._get_airbase_data(airport_code=self._vancouver)
        elif province == "NL":
            return self._get_airbase_data(airport_code=self._vancouver)
        elif province == "NS":
            return self._get_airbase_data(airport_code=self._vancouver)
        elif postal_code == self.__pc_inuvik:
            return self._northwest_territories()
        elif province == "NU":
            pass
        elif province == "ON":
            return self._get_airbase_data(airport_code=self._vancouver)
        elif province == "PE":
            return self._get_airbase_data(airport_code=self._vancouver)
        elif province == "QC":
            return self._get_airbase_data(airport_code=self._vancouver)
        elif province == "SK":
            return self._get_airbase_data(airport_code=self._vancouver)
        elif province == "YT":
            return self._yukon(postal_code=postal_code)

        return {}

    def get_airbase(self, o_province: str, o_postal_code: str, d_province: str, d_postal_code: str) -> tuple:

        mid_origin = self._get_airbase_single(province=o_province, postal_code=o_postal_code)
        mid_destination = self._get_airbase_single(province=d_province, postal_code=d_postal_code)

        return mid_origin, mid_destination

    @staticmethod
    def get_single_base(airport_code: str) -> dict:

        try:
            airbase = Airbase.objects.get(carrier__code=AIR_NORTH, code=airport_code)

            return airbase.get_ship_dict
        except ObjectDoesNotExist as e:
            connection.close()
            return {}
