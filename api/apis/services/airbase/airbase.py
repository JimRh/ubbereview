from api.apis.services.airbase.carrier_airbases.air_inuit_airbases import AirInuitAirbase
from api.apis.services.airbase.carrier_airbases.air_north import AirNorthAirbase
from api.apis.services.airbase.carrier_airbases.buffalo import BuffaloAirbase
from api.apis.services.airbase.carrier_airbases.calm_air_airbases import CalmAirAirbase
from api.apis.services.airbase.carrier_airbases.cargojet import CargojetAirbase
from api.apis.services.airbase.carrier_airbases.cn_airbase import CanadianNorthAirbase
from api.apis.services.airbase.carrier_airbases.perimeter_airbase import PerimeterAirbase
from api.apis.services.airbase.carrier_airbases.westjet_airbases import WestJetAirbase
from api.globals.carriers import CAN_NORTH, WESTJET, AIR_NORTH, CALM_AIR, CARGO_JET, PERIMETER_AIR, BUFFALO_AIRWAYS, \
    AIR_INUIT


class FindAirbase:

    @staticmethod
    def get_airbase(carrier_id: int, origin: dict, destination: dict) -> tuple:
        o_province = origin["province"]
        o_postal_code = origin["postal_code"].replace(" ", "").upper()

        d_province = destination["province"]
        d_postal_code = destination["postal_code"].replace(" ", "").upper()

        if carrier_id == CAN_NORTH:
            return CanadianNorthAirbase().get_airbase(
                o_province=o_province,
                o_postal_code=o_postal_code,
                d_province=d_province,
                d_postal_code=d_postal_code,
            )
        elif carrier_id == WESTJET:
            return WestJetAirbase().get_airbase(
                o_province=o_province,
                o_postal_code=o_postal_code,
                d_province=d_province,
                d_postal_code=d_postal_code,
            )
        elif carrier_id == AIR_NORTH:
            return AirNorthAirbase().get_airbase(
                o_province=o_province,
                o_postal_code=o_postal_code,
                d_province=d_province,
                d_postal_code=d_postal_code,
            )
        elif carrier_id == BUFFALO_AIRWAYS:
            return BuffaloAirbase().get_airbase(
                o_province=o_province,
                o_postal_code=o_postal_code,
                d_province=d_province,
                d_postal_code=d_postal_code,
            )
        elif carrier_id == CALM_AIR:
            return CalmAirAirbase().get_airbase(
                o_province=o_province,
                o_postal_code=o_postal_code,
                d_province=d_province,
                d_postal_code=d_postal_code,
            )
        elif carrier_id == CARGO_JET:
            return CargojetAirbase().get_airbase(
                o_province=o_province,
                o_postal_code=o_postal_code,
                d_province=d_province,
                d_postal_code=d_postal_code,
            )
        elif carrier_id == PERIMETER_AIR:
            return PerimeterAirbase().get_airbase(
                o_province=o_province,
                o_postal_code=o_postal_code,
                d_province=d_province,
                d_postal_code=d_postal_code,
            )
        elif carrier_id == AIR_INUIT:
            return AirInuitAirbase().get_airbase(
                o_province=o_province,
                o_postal_code=o_postal_code,
                d_province=d_province,
                d_postal_code=d_postal_code,
            )

        return {}, {}

    @staticmethod
    def get_airbase_by_code(carrier_id: int, origin_code: str, destination_code: str) -> tuple:

        if carrier_id == CAN_NORTH:

            if destination_code == "YOW":
                destination_code = "WOY"

            origin_base = CanadianNorthAirbase().get_single_base(airport_code=origin_code)
            destination_base = CanadianNorthAirbase().get_single_base(airport_code=destination_code)

            if destination_code == "WOY":
                destination_base["base"] = "YOW"

            return origin_base, destination_base
        elif carrier_id == WESTJET:
            origin_base = WestJetAirbase().get_single_base(airport_code=origin_code)
            destination_base = WestJetAirbase().get_single_base(airport_code=destination_code)

            return origin_base, destination_base
        elif carrier_id == AIR_NORTH:
            origin_base = AirNorthAirbase().get_single_base(airport_code=origin_code)
            destination_base = AirNorthAirbase().get_single_base(airport_code=destination_code)

            return origin_base, destination_base
        elif carrier_id == BUFFALO_AIRWAYS:
            origin_base = BuffaloAirbase().get_single_base(airport_code=origin_code)
            destination_base = BuffaloAirbase().get_single_base(airport_code=destination_code)

            return origin_base, destination_base
        elif carrier_id == CALM_AIR:
            origin_base = CalmAirAirbase().get_single_base(airport_code=origin_code)
            destination_base = CalmAirAirbase().get_single_base(airport_code=destination_code)

            return origin_base, destination_base
        elif carrier_id == CARGO_JET:
            origin_base = CargojetAirbase().get_single_base(airport_code=origin_code)
            destination_base = CargojetAirbase().get_single_base(airport_code=destination_code)

            return origin_base, destination_base
        elif carrier_id == PERIMETER_AIR:
            origin_base = PerimeterAirbase().get_single_base(airport_code=origin_code)
            destination_base = PerimeterAirbase().get_single_base(airport_code=destination_code)

            return origin_base, destination_base
        elif carrier_id == AIR_INUIT:
            origin_base = AirInuitAirbase().get_single_base(airport_code=origin_code)
            destination_base = AirInuitAirbase().get_single_base(airport_code=destination_code)

            return origin_base, destination_base

        return {}, {}
