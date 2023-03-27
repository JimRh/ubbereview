"""
Module for common contact utilities methods
This module contains contact utilities that are used in multiple apps.
Authors: Kenneth Carmichael (kencar17)
Date: February 27th 2023
Version: 1.0
"""
from apps.common.globals.project import TEN, EIGHT


def hash_contact(data: dict) -> str:
    """
    Hash the contact and return the result to be saved.
    @param data: Contact Dictionary
    @return: hash value
    """

    together = f'{data["company_name"]}{data["name"]}{data["phone"]}{data["email"]}'.replace(" ", "")

    return str(abs(hash(together)) % (TEN**EIGHT))
