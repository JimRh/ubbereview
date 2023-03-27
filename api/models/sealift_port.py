"""
    Title: Port Model
    Description: This file will contain functions for Port Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField
from django.db.models.fields.related import ForeignKey

from api.globals.project import DEFAULT_CHAR_LEN, AIRPORT_CODE_LEN
from api.models import Address
from api.models.base_table import BaseTable


class Port(BaseTable):
    """
        Port Model
    """

    # TODO Revise to be based off of GOV of Canada ports codes
    name = CharField(max_length=DEFAULT_CHAR_LEN * 2, default="", help_text="Port Name")
    address = ForeignKey(Address, on_delete=CASCADE, blank=True, null=True, related_name='port_address')
    code = CharField(max_length=AIRPORT_CODE_LEN, blank=True)

    class Meta:
        verbose_name = "Port"
        verbose_name_plural = "Ports"
        ordering = ["name"]

    @property
    def to_json(self) -> dict:
        """
            Get Port Address dict
            :return:
        """
        address_dict = self.address.get_ship_dict

        address_dict["port"] = self.name
        address_dict["base"] = self.code

        return address_dict

    @staticmethod
    def separate_ports(owned_ports: list) -> list:
        """
            Function will return a dictionary of carriers separated by type.
            :param owned_ports: list of Owned Port Objects
            :return: dict
        """
        ret = []

        for port in Port.objects.all():
            if port in owned_ports:
                selected = 'selected'
            else:
                selected = ''

            ret.append({"name": port.name, "code": port.code, "selected": selected})

        return ret

    # Override
    def __repr__(self) -> str:
        if self.address is None:
            return f"< Port ({self.name} - {self.code}: None, None) >"
        return f"< Port ({self.name} - {self.code}: {self.address.city}, {self.address.province.country.code}) >"

    # Override
    def __str__(self) -> str:
        if self.address is None:
            return f"{self.name} - {self.code}: None, None"
        return f"{self.name} - {self.code}: {self.address.city}, {self.address.province.country.code}"
