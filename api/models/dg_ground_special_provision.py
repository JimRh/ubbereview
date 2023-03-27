"""
    Title: DangerousGoodGroundSpecialProvision Model
    Description: This file will contain functions for DangerousGoodGroundSpecialProvision Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from api.models.dg_special_provision import DangerousGoodSpecialProvision


class DangerousGoodGroundSpecialProvision(DangerousGoodSpecialProvision):
    """
        DangerousGoodGroundSpecialProvision Model
    """

    class Meta:
        verbose_name = "Dangerous Good Ground Special Provision"
        ordering = ["code"]

    # Override
    def save(self, *args, **kwargs) -> None:
        self.clean_fields()
        self.validate_unique()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"<DangerousGoodGroundSpecialProvision ( {str(self.code)} ) >"

    # Override
    def __str__(self) -> str:
        return str(self.code)
