"""
    Title: Saved Package Model
    Description: This file will contain functions for Saved Package Model.
    Created: October 25, 2022
    Author: Yusuf Abdulla
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from django.db import models
from django.db.models.deletion import PROTECT
from django.db.models.fields.related import ForeignKey

from api.globals.project import MAX_CHAR_LEN, DIMENSION_PRECISION, MAX_DIMENSION_DIGITS, \
    WEIGHT_PRECISION, MAX_WEIGHT_DIGITS, LETTER_MAPPING_LEN, API_PACKAGE_TYPES
from api.models import SubAccount
from api.models.base_table import BaseTable


class SavedPackage(BaseTable):

    _BOX_TYPES = (
        ('ECOM_BOX', 'Ecommerce Box'),
        ('NORM_BOX', 'Normal Package'),
    )

    _PACKAGE_TYPES = API_PACKAGE_TYPES

    sub_account = ForeignKey(SubAccount, on_delete=PROTECT, help_text="The account the saved package belongs to.")
    box_type = models.CharField(max_length=LETTER_MAPPING_LEN * 10, choices=_BOX_TYPES, default="NORM_BOX", help_text="The saved package type.")
    package_type = models.CharField(max_length=LETTER_MAPPING_LEN * 10, choices=_PACKAGE_TYPES, default="BOX", help_text="The normal package type.")
    freight_class_id = models.DecimalField(decimal_places=DIMENSION_PRECISION, max_digits=MAX_DIMENSION_DIGITS, default=Decimal("-1.00"))
    description = models.CharField(max_length=MAX_CHAR_LEN, default="TEST", help_text="Description of the saved package.")
    length = models.DecimalField(decimal_places=DIMENSION_PRECISION, max_digits=MAX_DIMENSION_DIGITS, default=0, help_text="Metric value")
    width = models.DecimalField(decimal_places=DIMENSION_PRECISION, max_digits=MAX_DIMENSION_DIGITS, default=0, help_text="Metric value")
    height = models.DecimalField(decimal_places=DIMENSION_PRECISION, max_digits=MAX_DIMENSION_DIGITS, default=0, help_text="Metric value")
    weight = models.DecimalField(decimal_places=WEIGHT_PRECISION, max_digits=MAX_WEIGHT_DIGITS, default=0, help_text="Metric value")

    class Meta:
        verbose_name = "Saved Package"
        verbose_name_plural = "Saved Packages"

    @classmethod
    def create(cls, param_dict: dict = None):
        """
          Overrides create method. Creates new SavedPackage instance and sets sub_account to dict value
            :param param_dict: dict - Dictionary of keys
            :return: new SavedPackage instance
        """

        obj = cls()
        if param_dict is not None:
            obj.set_values(param_dict)
            obj.sub_account = param_dict.get('sub_account')
        return obj

    # Override
    def __repr__(self) -> str:
        return f"< Saved Package ({self.sub_account}: {self.length}x{self.width}x{self.height}, {self.weight} >"

    # Override
    def __str__(self) -> str:
        return f"{str(self.sub_account)}: {self.length}x{self.width}x{self.height}, {self.weight}"
