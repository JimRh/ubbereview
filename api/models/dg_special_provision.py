"""
    Title: DangerousGoodSpecialProvision Model
    Description: This file will contain functions for DangerousGoodSpecialProvision Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models.fields import PositiveSmallIntegerField, TextField

from api.models.base_table import BaseTable


class DangerousGoodSpecialProvision(BaseTable):
    """
        DangerousGoodSpecialProvision Model
    """

    code = PositiveSmallIntegerField(unique=True)
    description = TextField()

    class Meta:
        abstract = True
