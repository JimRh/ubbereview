"""
Module for common address utilities methods
This module contains address utilities that are used in multiple apps.
Authors: Kenneth Carmichael (kencar17)
Date: February 27th 2023
Version: 1.0
"""

import re

from apps.common.globals.project import DIRECTIONAL, TEN, EIGHT


def clean_address(address: str) -> str:
    """

    @param address:
    @return:
    """
    address = address.strip()

    address = re.sub(
        r"(\s)North West|north west|nw?(\s\Z|\Z)", r"\g<1>NW\g<2>", address
    )
    address = re.sub(
        r"(\s)North East|north east|ne?(\s\Z|\Z)", r"\g<1>NE\g<2>", address
    )
    address = re.sub(
        r"(\s)South East|south east|se?(\s\Z|\Z)", r"\g<1>SE\g<2>", address
    )
    address = re.sub(
        r"(\s)South West|south west|sw?(\s\Z|\Z)", r"\g<1>SW\g<2>", address
    )
    address = re.sub(r"(\s)East|east?(\s\Z|\Z)", r"\g<1>E\g<2>", address)
    address = re.sub(r"(\s)West|west?(\s\Z|\Z)", r"\g<1>W\g<2>", address)
    address = re.sub(r"(\s)South|south?(\s\Z|\Z)", r"\g<1>S\g<2>", address)
    address = re.sub(r"(\s)North|north?(\s\Z|\Z)", r"\g<1>N\g<2>", address)

    # Capitalize Everything except N,S,E,W
    new_address = ""

    for word in address.split():
        if word in DIRECTIONAL:
            new_address += f" {word.upper()}"
        else:
            new_address += f" {word.capitalize()}"

    address = new_address.strip()

    # Road Types
    address = re.sub(r"(\s)Avenue|avenue|ave?(\s\Z|\Z)", r"\g<1>Ave\g<2>", address)
    address = re.sub(r"(\s)Street|street|st(\s\Z|\Z)", r"\g<1>St\g<2>", address)
    address = re.sub(
        r"(\s)Boulevard|boulevard|blvd?(\s\Z|\Z)", r"\g<1>Blvd\g<2>", address
    )
    address = re.sub(r"(\s)Road|road|rd(\s\Z|\Z)", r"\g<1>Rd\g<2>", address)
    address = re.sub(r"(\s)Drive|drive|dr?(\s\Z|\Z)", r"\g<1>Dr\g<2>", address)

    return address


def clean_city(city: str) -> str:
    """
    Clean City by capitalizing first letter of each word and return result.
    @param city:
    @return:
    """
    return " ".join(w.capitalize() for w in city.split())


def clean_postal_code(postal_code: str) -> str:
    """
    Clean Postal Code by removing all spaces and uppercasing the letters.
    @param postal_code:
    @return:
    """
    return postal_code.upper().strip().replace(" ", "")


def hash_address(data: dict) -> str:
    """
    Hash the address and return the result to be saved.
    @param data: Address Dictionary
    @return: hash value
    """

    together = (
        f'{data["address"]}{data["city"]}{data["province"]["country"]["code"]}'
        f'{data["province"]["code"]}{data["postal_code"]}'.replace(" ", "")
    )

    return str(abs(hash(together)) % (TEN**EIGHT))
