"""
    Title: Contact Model
    Description: This file will contain functions for Contact Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models.fields import CharField, EmailField

from api.globals.project import DEFAULT_CHAR_LEN, MAX_CHAR_LEN
from api.models.base_table import BaseTable


class Contact(BaseTable):
    """
        Contact Model
    """

    company_name = CharField(max_length=DEFAULT_CHAR_LEN)
    name = CharField(max_length=MAX_CHAR_LEN)
    phone = CharField(max_length=DEFAULT_CHAR_LEN)
    extension = CharField(max_length=DEFAULT_CHAR_LEN, blank=True, null=True)
    email = EmailField()

    class Meta:
        ordering = ["name"]

    @classmethod
    def create_or_find(cls, param_dict: dict = None):
        """
            Create or Find Contact from passed in param dict
            :param param_dict: dict - Dictionary of keys
            :return: Contact Object
        """

        param_dict["name"] = param_dict.get("name", "").title()

        contact = Contact.find(param_dict=param_dict)

        if contact is None:
            contact = cls.create(param_dict=param_dict)
            contact.save()
        return contact

    @staticmethod
    def find(param_dict: dict):
        """
            Find Contact from passed in param dict
            :param param_dict: dict - Dictionary of keys
            :return: Contact Object
        """

        try:
            return Contact.objects.get(
                name=param_dict.get("name", ''),
                company_name=param_dict.get("company_name", ""),
                phone=param_dict.get("phone", ""),
                email=param_dict.get("email", "")
            )
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            return None

    def next_leg_json(self) -> dict:
        return {
            "name": self.name,
            "company_name": self.company_name,
            "phone": self.phone,
            "email": self.email
        }

    # Override
    def __repr__(self) -> str:
        return f"< Contact ( {self.name} ) >"

    # Override
    def __str__(self) -> str:
        return self.name
