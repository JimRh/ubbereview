"""
    Title: DangerousGood Model
    Description: This file will contain functions for DangerousGood Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from django.db.models.deletion import PROTECT
from django.db.models.fields import PositiveSmallIntegerField, CharField, TextField, DecimalField, BooleanField
from django.db.models.fields.related import ManyToManyField, ForeignKey

from api.globals.project import LETTER_MAPPING_LEN, BASE_TEN, MAX_CHAR_LEN
from api.models import DangerousGoodClassification, DangerousGoodGenericLabel, DangerousGoodPackingGroup, \
    DangerousGoodExceptedQuantity, DangerousGoodAirCutoff, DangerousGoodAirSpecialProvision, \
    DangerousGoodGroundSpecialProvision
from api.models.base_table import BaseTable


# TODO: Review DG tables, split Air, Ground, Ocean (Future)
class DangerousGood(BaseTable):
    """
        DangerousGood Model
    """
    _sig_fig = Decimal(str(BASE_TEN ** (3 * -1)))
    _UNIT_MEASURE_TYPES = (
        ("K", "Mass"),
        ("V", "Volume")
    )

    _STATE = (
        ("S", "Solid"),
        ("L", "Liquid"),
        ("G", "Gas")
    )

    un_number = PositiveSmallIntegerField()
    # TODO: Improve dg dec to be more dynamic to handle longer proper names
    short_proper_shipping_name = CharField(max_length=120)
    verbose_proper_shipping_name = TextField(blank=True)
    identification_details = CharField(max_length=MAX_CHAR_LEN, blank=True)
    classification = ForeignKey(
        DangerousGoodClassification, on_delete=PROTECT, related_name="dangerousgood_classification"
    )
    subrisks = ManyToManyField(
        DangerousGoodClassification,
        blank=True,
        related_name="dangerousgood_subrisks",
        help_text="Additional minor Class(s)/Div(s) contained in the dg."
    )
    specialty_label = ForeignKey(
        DangerousGoodGenericLabel,
        on_delete=PROTECT,
        null=True,
        blank=True,
        related_name="dangerousgood_specialty_label",
        help_text="Labels such as 'Magnetic', 'Cryogenic', etc.."
    )
    packing_group = ForeignKey(
        DangerousGoodPackingGroup, on_delete=PROTECT, related_name="dangerousgood_packing_group"
    )
    excepted_quantity = ForeignKey(
        DangerousGoodExceptedQuantity, on_delete=PROTECT, related_name="dangerousgood_excepted_quantity"
    )
    unit_measure = CharField(
        max_length=LETTER_MAPPING_LEN, choices=_UNIT_MEASURE_TYPES, help_text="Mass unit: KG. Volume unit: L"
    )
    air_quantity_cutoff = ManyToManyField(DangerousGoodAirCutoff, related_name="dangerousgood_air_quantity_cutoff")
    ground_limited_quantity_cutoff = DecimalField(
        decimal_places=3, max_digits=6, help_text="0 indicates forbidden"
    )
    ground_maximum_quantity_cutoff = DecimalField(
        decimal_places=3, max_digits=6, help_text="0 indicates forbidden"
    )
    air_special_provisions = ManyToManyField(
        DangerousGoodAirSpecialProvision, blank=True, related_name="dangerousgood_air_special_provisions"
    )
    ground_special_provisions = ManyToManyField(
        DangerousGoodGroundSpecialProvision, blank=True, related_name="dangerousgood_ground_special_provisions"
    )
    is_gross_measure = BooleanField(default=False, help_text="Is the limited quantity measure a gross measurement")
    is_ground_exempt = BooleanField(default=False)
    is_nos = BooleanField(default=False)
    is_neq = BooleanField(default=False)
    state = CharField(
        max_length=LETTER_MAPPING_LEN,
        choices=_STATE,
        default="S",
        help_text="State of the DG: Solid, Liquid, Gas"
    )

    class Meta:
        verbose_name = "Dangerous Good"
        ordering = ["un_number", "packing_group"]
        unique_together = ("un_number", "short_proper_shipping_name", "packing_group")

    @staticmethod
    def get_data(unnumber: int) -> dict:
        """
            Get DG information
            :param unnumber: int
            :return: dict of dg datas
        """
        data = {}
        is_nos = False
        is_neq = False

        dgs = DangerousGood.objects.filter(un_number=unnumber)

        if not dgs:
            return {}

        proper_shipping_name = set()

        for dg in dgs:
            proper_shipping_name.add(dg.short_proper_shipping_name)
            is_nos = dg.is_nos
            is_neq = dg.is_neq

            group_name = dg.packing_group.get_packing_group_display() + ": " + dg.packing_group.description

            if dg.short_proper_shipping_name in data:
                data[dg.short_proper_shipping_name].append({
                    "code": dg.packing_group.packing_group,
                    "details": group_name
                })
            else:
                data[dg.short_proper_shipping_name] = [{
                    "code": dg.packing_group.packing_group,
                    "details": group_name
                }]

        return {
            "proper_shipping_names": list(proper_shipping_name),
            "is_nos": is_nos,
            "is_neq": is_neq,
            "shipping_name_data": data
        }

    # TODO - CLEAN UP
    def subrisks_str(self) -> str:
        """
            Join all sub risks into a str
            :return:
        """

        subrisks = [
            subrisk.verbose_classification()
            for subrisk in self.subrisks.all()
        ]

        if subrisks:
            return "(" + ", ".join(subrisks) + ")"
        return ''

    # Override
    def save(self, *args, **kwargs) -> None:
        self.ground_limited_quantity_cutoff = self.ground_limited_quantity_cutoff.quantize(self._sig_fig)
        self.ground_maximum_quantity_cutoff = self.ground_maximum_quantity_cutoff.quantize(self._sig_fig)
        self.clean_fields()
        self.validate_unique()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< DangerousGood (UN{self.un_number}: {self.short_proper_shipping_name}) >"

    # Override
    def __str__(self) -> str:
        return f"UN{self.un_number}: {self.short_proper_shipping_name}"
