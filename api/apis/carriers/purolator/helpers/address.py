"""
    Title: Purolator Address
    Description: This file will contain helper functions related to Purolator addresss specs.
    Created: November 19, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import phonenumbers

from api.apis.carriers.purolator.courier.endpoints.purolator_service import (
    PurolatorService,
)


class PurolatorAddress:
    """
    Purolator Address
    """

    _street_types = {
        "abbey",
        "end",
        "montéé",
        "village",
        "acres",
        "esplanade",
        "mount",
        "villas",
        "allée",
        "estates",
        "mountain",
        "vista",
        "alley",
        "expressway",
        "parade",
        "voie",
        "autoroute",
        "extension",
        "parc",
        "walk",
        "avenue",
        "field",
        "park",
        "way",
        "avenue",
        "forest",
        "parkway",
        "wharf",
        "bay",
        "freeway",
        "passage",
        "wood",
        "beach",
        "front",
        "path",
        "wynd",
        "bend",
        "gardens",
        "pathway",
        "boulevard",
        "gate",
        "pines",
        "branch",
        "glade",
        "place",
        "by-pass",
        "by pass",
        "glen",
        "plateau",
        "campus",
        "green",
        "plaza",
        "cape",
        "grounds",
        "point",
        "carré",
        "grove",
        "pointe",
        "carrefour",
        "harbour",
        "port",
        "centre",
        "heath",
        "private",
        "cercle",
        "height",
        "promenade",
        "chase",
        "heights",
        "quai",
        "chemin",
        "highlands",
        "quay",
        "circle",
        "highway",
        "ramp",
        "circuit",
        "hill",
        "rang",
        "close",
        "hollow",
        "ridge",
        "common",
        "île",
        "rise",
        "concession",
        "impasse",
        "road",
        "corners",
        "inlet",
        "route",
        "côte",
        "island",
        "row",
        "cour",
        "key",
        "rue",
        "cours",
        "knoll",
        "ruelle",
        "court",
        "landing",
        "run",
        "cove",
        "lane",
        "sentier",
        "crest",
        "limits",
        "square",
        "crescent",
        "line",
        "street",
        "croissant",
        "link",
        "subdivision",
        "crossing",
        "lookout",
        "terrace",
        "cul-de-sac",
        "cul de sac",
        "loop",
        "terrasse",
        "dale",
        "mall",
        "townline",
        "dell",
        "manor",
        "trail",
        "diversion",
        "maze",
        "turnabout",
        "downs",
        "meadow",
        "vale",
        "drive",
        "mews",
        "view",
    }

    saved_address_version = {
        "st": "street",
        "rd": "Road",
        "ave": "Avenue",
        "blvd": "boulevard",
        "dr": "drive"
    }

    def __init__(self, is_rate: bool, ubbe_request: dict) -> None:
        self._is_rate = is_rate
        self._puro_validate = PurolatorService(ubbe_request=ubbe_request)

    def _validate_address(self, address: dict) -> dict:
        """
        validates that the city/province (state)/postal (zip) code entered is correct
        :param address:
        :return:
        """

        try:
            validated = self._puro_validate.validate_city_postal(address=address)
        except Exception:
            return {}

        return validated

    def _get_street_info(self, address: str) -> tuple:
        """
        Get street number andd street type.
        :param address:
        :return:
        """
        address = address.replace("-", " ") + " 0"
        components = []
        street_type = "road"

        for i, com in enumerate(address.split(" ")):
            if com.isdigit():
                components.append(com)

            if com.lower() in self._street_types:
                street_type = com
            elif com.lower() in self.saved_address_version:
                street_type = self.saved_address_version[com.lower()]

        return components[0][:6], street_type.title()

    def address(self, address: dict) -> dict:
        """
        Create puro address soap object.
        :param address: address in ubbe request.
        :return:
        """

        street_number, street_type = self._get_street_info(address=address["address"])
        validated = self._validate_address(address=address)

        if validated:
            address["city"] = validated["city"]

        ret = {
            "Name": address.get("name", "BBE")[:30],
            "Company": address.get("company_name", "BBE")[:30],
            "StreetNumber": street_number,
            "StreetName": address["address"].replace(street_number, "").strip(),
            "StreetType": street_type,
            "StreetAddress2": address.get("address_two", ""),
            "City": address["city"],
            "Province": address["province"],
            "Country": address["country"],
            "PostalCode": str(address["postal_code"]).replace(" ", "").upper(),
        }

        # Only add phone when its shipping, otherwise Estimate api doesn't require it.
        if not self._is_rate:
            number = phonenumbers.parse(address["phone"], address["country"])

            ret.update(
                {
                    "PhoneNumber": {
                        "CountryCode": number.country_code,
                        "AreaCode": str(number.national_number)[:3],
                        "Phone": str(number.national_number)[3:],
                        "Extension": address.get("extension", ""),
                    }
                }
            )

        return ret
