"""
    Title: DangerousGoodSpecialProvision Model
    Description: This file will contain functions for DangerousGoodSpecialProvision Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models.fields import TextField, BooleanField

from api.models.dg_special_provision import DangerousGoodSpecialProvision


class DangerousGoodAirSpecialProvision(DangerousGoodSpecialProvision):
    """
        DangerousGoodSpecialProvision Model
    """

    note = TextField(blank=True)
    is_non_restricted = BooleanField(default=False)

    class Meta:
        verbose_name = "Dangerous Good Air Special Provision"
        ordering = ["code"]

    # Override
    def save(self, *args, **kwargs) -> None:
        self.clean_fields()
        self.validate_unique()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"<DangerousGoodAirSpecialProvision (A {str(self.code)} ) >"

    # Override
    def __str__(self) -> str:
        return f"A{str(self.code)}"
