"""
    Title: Package Type Model
    Description: This file will contain views that only relate to Package Type Model.
    Created: Jan 25, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from django.db.models import ForeignKey, PROTECT, BooleanField, ManyToManyField
from django.db.models.fields import CharField, DecimalField

from api.globals.project import PRICE_PRECISION, BASE_TEN, PERCENTAGE_PRECISION, DEFAULT_CHAR_LEN, \
    DIMENSION_PRECISION, MAX_DIMENSION_DIGITS
from api.models import Account, SubAccount, Carrier
from api.models.base_table import BaseTable


class PackageType(BaseTable):

    _cost_sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))
    _percentage_sig_fig = Decimal(str(BASE_TEN ** (PERCENTAGE_PRECISION * -1)))

    account = ForeignKey(Account, on_delete=PROTECT, related_name='sub_account_package_type')
    code = CharField(
        max_length=DEFAULT_CHAR_LEN, help_text="Package Type Code: Must match Business Central Package Types. SKID"
    )
    name = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Package Type display name: Pallet, Skid")
    min_overall_dims = DecimalField(
        decimal_places=DIMENSION_PRECISION,
        default=Decimal("0"),
        blank=True,
        max_digits=MAX_DIMENSION_DIGITS,
        help_text="Min overall dimensions: L * (2W) * (H) Probably delete."
    )
    max_overall_dims = DecimalField(
        decimal_places=DIMENSION_PRECISION,
        max_digits=MAX_DIMENSION_DIGITS,
        help_text="Max overall dimensions: L * (2W) * (H)"
    )
    min_weight = DecimalField(
        decimal_places=DIMENSION_PRECISION,
        default=Decimal("0"),
        blank=True,
        max_digits=MAX_DIMENSION_DIGITS,
        help_text="Min Weight for package type."
    )
    max_weight = DecimalField(
        decimal_places=DIMENSION_PRECISION,
        max_digits=MAX_DIMENSION_DIGITS,
        help_text="Max Weight for package type."
    )
    is_common = BooleanField(default=False, help_text="Is the package type to be displayed in the common section?")
    is_dangerous_good = BooleanField(default=False, help_text="Is the package type a dangerous goods?")
    is_pharma = BooleanField(default=False, help_text="Is the package type a pharma goods?")
    is_active = BooleanField(default=False, help_text="Is the package type active other words allowed?")

    carrier = ManyToManyField(
        Carrier,
        related_name="carrier_package_type",
        help_text="Carriers allowed for this package type."
    )

    class Meta:
        verbose_name = 'Package Type'
        verbose_name_plural = 'Package Type\'s'
        ordering = ["account", "name"]

    # Override
    def save(self, *args, **kwargs) -> None:
        self.min_overall_dims = self.min_overall_dims.quantize(self._cost_sig_fig)
        self.max_overall_dims = self.max_overall_dims.quantize(self._cost_sig_fig)
        self.min_weight = self.min_weight.quantize(self._cost_sig_fig)
        self.max_weight = self.max_weight.quantize(self._percentage_sig_fig)

        self.clean_fields()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< PackageType ({self.account}: {self.name}, {self.is_common}, {self.is_active}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.account}: {self.name}, Common: {self.is_common}, Active: {self.is_active}"
