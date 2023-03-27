from api.exceptions.project import ViewException


class CanadaPostalCodeValidate:
    _CA = "CA"
    _US = "US"

    _nt_communities = [
        "aklavik", "behchoko", "colville lake", "deline", "enterprise", "fort good hope", "fort liard",
        "fort mcpherson", "fort providence", "fort resolution", "fort simpson", "fort smith", "gameti", "hay river",
        "inuvik", "jean marie river", "kakisa", "katl’odeeche", "nahanni butte", "norman wells", "paulatuk",
        "sachs harbour", "sambaa k'e", "tsiigehtchic", "tuktoyaktuk", "tuk", "tulita", "ulukhaktok", "wekweeti",
        "whati", "wrigley", "lutselk'e", "yellowknife", "deline", "déline"
    ]
    _nu_communities = [
        "arctic bay", "arviat", "baker lake", "cambridge bay", "cape dorset", "chesterfield inlet", "clyde river",
        "coral harbour", "grise fiord", "gjoa haven", "igloolik", "iqaluit", "kimmirut", "kugaaruk", "kugluktuk",
        "naujaat", "pangnirtung", "pond inlet", "qikiqtarjuaq", "rankin inlet", "resolute bay", "sanikiluaq",
        "taloyoak", "whale cove", "hall beach", "kinngait", "sanirajak"
    ]

    @staticmethod
    def _check_postal(postal_letter, province):

        if province == "AB":
            return postal_letter.upper() == "T"
        elif province == "BC":
            return postal_letter.upper() == "V"
        elif province == "MB":
            return postal_letter.upper() == "R"
        elif province == "NB":
            return postal_letter.upper() == "E"
        elif province == "NL":
            return postal_letter.upper() == "A"
        elif province == "NS":
            return postal_letter.upper() == "B"
        elif province == "NT":
            return postal_letter.upper() == "X"
        elif province == "NU":
            return postal_letter.upper() == "X"
        elif province == "ON":
            return postal_letter.upper() in set("PLNMK")
        elif province == "PE":
            return postal_letter.upper() == "C"
        elif province == "QC":
            return postal_letter.upper() in set("JGHK")
        elif province == "SK":
            return postal_letter.upper() == "S"
        elif province == "YT":
            return postal_letter.upper() == "Y"

        return False

    @staticmethod
    def _check_nt_community_postal(postal_code: str, city: str) -> bool:
        """
            Check NT province communities and postal code for mismatches.
            :param postal_code: Postal Code
            :param city: City
            :return: bool
        """

        if city.lower() == "aklavik":
            return postal_code == "X0E0A0"
        elif city.lower() == "behchoko":
            return postal_code == "X0E0Y0"
        elif city.lower() == "colville lake":
            return postal_code == "X0E1L0"
        elif city.lower() == "deline" or city.lower() == "déline":
            return postal_code == "X0E0G0"
        elif city.lower() == "enterprise":
            return postal_code == "X0E0R1"
        elif city.lower() == "fort good hope":
            return postal_code == "X0E0H0"
        elif city.lower() == "fort liard":
            return postal_code in ["X0E0R6", "X0G0A0"]
        elif city.lower() == "fort mcpherson":
            return postal_code == "X0E0J0"
        elif city.lower() == "fort providence":
            return postal_code == "X0E0L0"
        elif city.lower() == "fort resolution":
            return postal_code == "X0E0M0"
        elif city.lower() == "fort simpson":
            return postal_code == "X0E0N0"
        elif city.lower() == "fort smith":
            return postal_code in ["X0E0P0"]
        elif city.lower() == "gameti":
            return postal_code == "X0E1R0"
        elif city.lower() == "hay river":
            return postal_code in [
                "X0E0R9", "X0E0R5", "X0E0R0", "X0E0R2", "X0E0R3", "X0E0R4", "X0E0R6", "X0E0R7", "X0E0R8", "X0E0R9",
                'X0E1G1', "X0E1G2", "X0E1G3", "X0E1G4", "X0E1G5"
            ]
        elif city.lower() == "inuvik":
            return postal_code == "X0E0T0"
        elif city.lower() == "jean marie river":
            return postal_code == "X0E0N0"
        elif city.lower() == "kakisa":
            return postal_code == "X0E1G4"
        elif city.lower() == "katl’odeeche":
            return postal_code == "X0E1G4"
        elif city.lower() == "nahanni butte":
            return postal_code == "X0E0N0"
        elif city.lower() == "norman wells":
            return postal_code == "X0E0V0"
        elif city.lower() == "paulatuk":
            return postal_code == "X0E1N0"
        elif city.lower() == "sachs harbour":
            return postal_code == "X0E0Z0"
        elif city.lower() == "sambaa k'e":
            return postal_code == "X0E1Z0"
        elif city.lower() == "tsiigehtchic":
            return postal_code == "X0E0B0"
        elif city.lower() == "tuktoyaktuk" or city.lower() == "tuk":
            return postal_code == "X0E1C0"
        elif city.lower() == "tulita":
            return postal_code == "X0E0K0"
        elif city.lower() == "ulukhaktok":
            return postal_code == "X0E0S0"
        elif city.lower() == "wekweeti":
            return postal_code == "X0E1W0"
        elif city.lower() == "whati":
            return postal_code == "X0E1P0"
        elif city.lower() == "wrigley":
            return postal_code == "X0E1E0"
        elif city.lower() == "yellowknife":
            return postal_code.startswith("X1A")
        elif city.lower() == "lutselk'e":
            return postal_code == "X0E1A0"

        return False

    @staticmethod
    def _check_nu_community_postal(postal_code: str, city: str) -> bool:
        """
            Check NU province communities and postal code for mismatches.
            :param postal_code: Postal Code
            :param city: City
            :return: bool
        """
        if city.lower() == "arctic bay":
            return postal_code == "X0A0A0"
        elif city.lower() == "arviat":
            return postal_code == "X0C0E0"
        elif city.lower() == "baker lake":
            return postal_code == "X0C0A0"
        elif city.lower() == "cambridge bay":
            return postal_code == "X0B0C0"
        elif city.lower() == "cape dorset" or city.lower() == "kinngait":
            return postal_code == "X0A0C0"
        elif city.lower() == "chesterfield inlet":
            return postal_code == "X0C0B0"
        elif city.lower() == "clyde river":
            return postal_code == "X0A0E0"
        elif city.lower() == "coral harbour":
            return postal_code == "X0C0C0"
        elif city.lower() == "grise fiord":
            return postal_code == "X0A0J0"
        elif city.lower() == "gjoa haven":
            return postal_code == "X0B1J0"
        elif city.lower() == "hall beach" or city.lower() == "sanirajak":
            return postal_code == "X0A0K0"
        elif city.lower() == "igloolik":
            return postal_code == "X0A0L0"
        elif city.lower() == "kimmirut":
            return postal_code == "X0A0N0"
        elif city.lower() == "kugaaruk":
            return postal_code == "X0B1K0"
        elif city.lower() == "kugluktuk":
            return postal_code == "X0B0E0"
        elif city.lower() == "naujaat":
            return postal_code == "X0C0H0"
        elif city.lower() == "pangnirtung":
            return postal_code == "X0A0R0"
        elif city.lower() == "pond inlet":
            return postal_code == "X0A0S0"
        elif city.lower() == "qikiqtarjuaq":
            return postal_code == "X0A0B0"
        elif city.lower() == "rankin inlet":
            return postal_code == "X0C0G0"
        elif city.lower() == "resolute bay":
            return postal_code == "X0A0V0"
        elif city.lower() == "sanikiluaq":
            return postal_code == "X0A0W0"
        elif city.lower() == "taloyoak":
            return postal_code == "X0B1B0"
        elif city.lower() == "whale cove":
            return postal_code == "X0C0J0"
        elif city.lower() == "iqaluit":
            return postal_code in ["X0A0H0", "X0A1H0"]

        return False

    def validate(self, city: str, postal_code: str, province: str) -> bool:
        """

            :param city:
            :param postal_code:
            :param province:
            :return:
        """
        errors = []

        if not self._check_postal(postal_letter=postal_code[0], province=province):
            errors.append({"postal_code": f"Postal Code ({postal_code}) - Province ({province}) Mismatch."})

        if city not in self._nt_communities and province == "NT":
            errors.append({"city": f"Community ({city}) - Province ({province}) Mismatch."})
        elif not city.lower() in self._nu_communities and province == "NU":
            errors.append({"city": f"Community ({city}) - Province ({province}) Mismatch."})

        if province == "NT" and not self._check_nt_community_postal(postal_code=postal_code, city=city):
            errors.append({"postal_code": f"Community ({city}) - Postal Code ({postal_code}) Mismatch."})
        elif province == "NU" and not self._check_nu_community_postal(postal_code=postal_code, city=city):
            errors.append({"postal_code": f"Community ({city}) - Postal Code ({postal_code}) Mismatch."})

        if errors:
            raise ViewException(code="XXXXX", message="CA Postal Code Invalid.", errors=errors)

        return True
