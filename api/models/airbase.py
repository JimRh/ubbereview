"""
    Title: Airbase Model
    Description: This file will contain functions for Airbase Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField
from django.db.models.fields.related import ForeignKey

from api.globals.project import AIRPORT_CODE_LEN
from api.models import Address
from api.models.base_table import BaseTable


class Airbase(BaseTable):
    """
        Airbase Model
    """

    address = ForeignKey(Address, on_delete=CASCADE, blank=True, null=True, related_name='airbase_address')
    carrier = ForeignKey('Carrier', on_delete=CASCADE, related_name='airbase_carrier')
    code = CharField(max_length=AIRPORT_CODE_LEN, blank=True)

    class Meta:
        unique_together = ('code', 'carrier')

    @classmethod
    def create(cls, param_dict: dict = None):
        """
            Create Airbase from passed in param dict
            :param param_dict: dict - Dictionary of keys
            :return: Airbase Object
        """

        obj = cls()
        if param_dict is not None:
            obj.set_values(param_dict)
            obj.address = param_dict.get('address')
            obj.carrier = param_dict.get('carrier')
        return obj

    @property
    def get_ship_dict(self) -> dict:
        """

            :return: dict of address details
        """

        ret = self.address.get_ship_dict
        ret["base"] = self.code
        return ret

    # Override
    def save(self, *args, **kwargs) -> None:
        self.clean_fields()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        c_name = self.carrier.name

        if self.address is None:
            return f"< Airbase ({self.code}, {c_name}: None, None) >"
        return f"< Airbase ({self.code}, {c_name}: {self.address.city}, {self.address.province.country.code}) >"

    # Override
    def __str__(self) -> str:
        if self.address is None:
            return f"{self.code}, {self.carrier}: None, None"
        return f"{self.code}, {self.carrier}: {self.address.city}, {self.address.province.country.code}"
