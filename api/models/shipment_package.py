"""
    Title: Package Model
    Description: This file will contain functions for Package Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField, BooleanField, DecimalField, PositiveSmallIntegerField
from django.db.models.fields.related import ForeignKey

from api.general.convert import Convert
from api.globals.project import MAX_CHAR_LEN, BASE_TEN, WEIGHT_PRECISION, DIMENSION_PRECISION, MAX_PACK_ID_LEN, \
    MAX_DIMENSION_DIGITS, MAX_WEIGHT_DIGITS, LETTER_MAPPING_LEN, DG_PRECISION, MAX_WEIGHT_BREAK_DIGITS, \
    API_PACKAGE_TYPES, API_PACKAGE_CONTAINER_PACKING, API_PACKAGE_YES_NO
from api.models import DangerousGoodPackingGroup, DangerousGoodPackagingType, DangerousGoodClassification
from api.models.base_table import BaseTable


class Package(BaseTable):
    """
        Package Model
    """
    _weight_sig_fig = Decimal(str(BASE_TEN ** (WEIGHT_PRECISION * -1)))
    _dim_sig_fig = Decimal(str(BASE_TEN ** (DIMENSION_PRECISION * -1)))

    _PACKAGE_TYPES = API_PACKAGE_TYPES
    _CONTAINER_PACKING = API_PACKAGE_CONTAINER_PACKING
    _YES_NO = API_PACKAGE_YES_NO

    package_id = CharField(max_length=MAX_PACK_ID_LEN)
    package_account_id = CharField(
        max_length=MAX_PACK_ID_LEN,
        unique=True,
        help_text="External Tracking identifier for the package.",
        null=True,
        blank=True
    )
    shipment = ForeignKey("Shipment", on_delete=CASCADE, related_name='package_shipment')
    width = DecimalField(decimal_places=DIMENSION_PRECISION, max_digits=MAX_DIMENSION_DIGITS, help_text="Metric value")
    length = DecimalField(decimal_places=DIMENSION_PRECISION, max_digits=MAX_DIMENSION_DIGITS, help_text="Metric value")
    height = DecimalField(decimal_places=DIMENSION_PRECISION, max_digits=MAX_DIMENSION_DIGITS, help_text="Metric value")
    weight = DecimalField(decimal_places=WEIGHT_PRECISION, max_digits=MAX_WEIGHT_DIGITS)
    quantity = PositiveSmallIntegerField()
    package_type = CharField(max_length=LETTER_MAPPING_LEN * 10, choices=_PACKAGE_TYPES)
    description = CharField(max_length=MAX_CHAR_LEN)

    # TODO: Remove, unused?
    freight_class_id = DecimalField(
        decimal_places=DIMENSION_PRECISION, max_digits=MAX_DIMENSION_DIGITS, default=Decimal("-1.00")
    )

    un_number = PositiveSmallIntegerField(default=0, help_text="0 defines package is not a dangerous good")
    packing_group = ForeignKey(
        DangerousGoodPackingGroup,
        on_delete=CASCADE,
        null=True,
        blank=True,
        related_name="package_packing_group",
        help_text="Null defines package is not a dangerous good"
    )
    packing_type = ForeignKey(
        DangerousGoodPackagingType,
        on_delete=CASCADE,
        null=True,
        blank=True,
        related_name="package_packing_type",
        help_text="Null defines package is not a dangerous good"
    )
    dg_proper_name = CharField(max_length=MAX_CHAR_LEN, blank=True)
    dg_quantity = DecimalField(
        decimal_places=DG_PRECISION,
        max_digits=MAX_WEIGHT_BREAK_DIGITS,
        default=Decimal("0.00"),
        help_text="The specific quantity of dg product, separate from the packaging. 0 defines no dg."
    )
    dg_nos_description = CharField(max_length=MAX_CHAR_LEN, default="", blank=True)
    is_cooler = BooleanField(default=False)
    is_frozen = BooleanField(default=False)

    container_number = CharField(max_length=MAX_CHAR_LEN, default="", blank=True)
    container_pack = CharField(choices=_CONTAINER_PACKING, default='NA', max_length=LETTER_MAPPING_LEN * 10)
    vehicle_condition = CharField(
        choices=_YES_NO,
        default='NA',
        max_length=LETTER_MAPPING_LEN * 10,
        help_text="Is the Vehicle Running?"
    )
    anti_theft = CharField(
        choices=_YES_NO,
        default='NA',
        max_length=LETTER_MAPPING_LEN * 10,
        help_text="Does the Vehicle have anti theft?"
    )
    year = CharField(max_length=MAX_CHAR_LEN, default="", blank=True)
    make = CharField(max_length=MAX_CHAR_LEN, default="", blank=True)
    vin = CharField(max_length=MAX_CHAR_LEN, default="", blank=True)

    is_pharma = BooleanField(default=False)
    is_time_sensitive = BooleanField(default=False)
    is_cos = BooleanField(default=False)
    time_sensitive_hours = CharField(max_length=MAX_CHAR_LEN, default="", blank=True)

    class Meta:
        verbose_name = "Package"
        verbose_name_plural = "Shipment - Packages"

    @staticmethod
    def one_step_save(packages: list, shipment) -> None:
        package_objs = []

        for i, package in enumerate(packages):
            new_package = Package()

            new_package.package_id = "{}-{}".format(shipment.shipment_id, i + 1)
            new_package.shipment = shipment
            new_package.width = Decimal(package['width'])
            new_package.length = Decimal(package['length'])
            new_package.height = Decimal(package['height'])
            new_package.weight = Decimal(package['weight'])
            new_package.quantity = package['quantity']
            new_package.description = package['description']
            new_package.is_cooler = package.get('is_cooler', False)
            new_package.is_frozen = package.get('is_frozen', False)
            new_package.package_type = package.get('package_type', 'BOX')

            if package.get('freight_class_id'):
                new_package.freight_class_id = package.get('freight_class_id', Decimal("-1.00"))
            else:
                new_package.freight_class_id = Decimal("-1.00")

            if package.get("un_number", 0):
                new_package.un_number = package["un_number"]
                new_package.packing_group = DangerousGoodPackingGroup.objects.get(packing_group=package["packing_group"])
                new_package.packing_type = DangerousGoodPackagingType.objects.get(code=package["packing_type"])
                new_package.dg_quantity = package["dg_quantity"]
                new_package.dg_proper_name = package["proper_shipping_name"]

                if package["is_nos"]:
                    new_package.dg_nos_description = package["nos"]

            if package.get("is_pharma", False):
                new_package.is_pharma = package["is_pharma"]
                new_package.is_time_sensitive = package["is_time_sensitive"]
                new_package.is_cos = package["is_cos"]
                new_package.time_sensitive_hours = package.get('time_sensitive_hours', '')

            if new_package.package_type == "CONTAINER":
                new_package.container_number = package.get('container_number', '')
                new_package.container_pack = package.get('status', 'NA')
            elif new_package.package_type == "VEHICLE":
                new_package.vehicle_condition = package.get('condition', 'NA')
                new_package.anti_theft = package.get('anti_theft', 'NA')
                new_package.year = package.get('year', '')
                new_package.make = package.get('model', '')
                new_package.vin = package.get('vin', '')
            elif new_package.package_type == "SKID":
                new_package.freight_class_id = package.get('freight_class')

            if shipment.account_id:
                new_package.package_account_id = f'{shipment.account_id}-p{i + 1}'

            package_objs.append(copy.deepcopy(new_package))
        Package.objects.bulk_create(package_objs)

    def next_leg_json(self) -> dict:
        next_leg_json = {
            "width": self.width,
            "length": self.length,
            "height": self.height,
            "weight": self.weight,
            "quantity": self.quantity,
            "description": self.description,
            "imperial_length": Convert().cms_to_inches(self.length),
            "imperial_width": Convert().cms_to_inches(self.width),
            "imperial_height": Convert().cms_to_inches(self.height),
            "imperial_weight": Convert().kgs_to_lbs(self.weight),
            "is_dangerous_good": self.un_number != 0,
        }

        if self.is_cooler:
            next_leg_json["is_cooler"] = self.is_cooler

        if self.is_frozen:
            next_leg_json["is_frozen"] = self.is_frozen

        if self.un_number:
            next_leg_json["un_number"] = self.un_number
            next_leg_json["dg_class"] = DangerousGoodClassification.objects.get(
                dangerousgood_classification__un_number=self.un_number,
                dangerousgood_classification__packing_group=self.packing_group
            )

        if self.package_type:
            next_leg_json["package_type"] = self.package_type

        if self.is_pharma:
            next_leg_json["is_time_sensitive"] = self.is_time_sensitive
            next_leg_json["is_cos"] = self.is_cos

            if self.is_time_sensitive:
                next_leg_json["time_sensitive_hours"] = self.time_sensitive_hours

        return next_leg_json

    def to_json(self) -> dict:
        """
            Function will return details about the object in dictionary form
            :return: dict
        """
        ret = {
            "package_id": self.package_id,
            "quantity": self.quantity,
            "description": self.description,
            "package_type": self.package_type,
            "length": self.length,
            "width": self.width,
            "height": self.height,
            "weight": self.weight,
            "is_cooler": self.is_cooler,
            "is_frozen": self.is_frozen,
            "dangerous_goods": "No"
        }

        if self.un_number != 0:
            ret["is_dangerous_goods"] = True
            ret["dangerous_goods"] = "Yes"
            ret["dg_quantity"] = self.dg_quantity
            ret["un_number"] = self.un_number
            ret["packing_group"] = self.packing_group.packing_group
            ret["packing_group_str"] = self.packing_group.get_packing_group_display()
            ret["packing_type"] = self.packing_type.code
            ret["proper_shipping_name"] = self.dg_proper_name

            is_nos = self.dg_nos_description != ""

            if is_nos:
                ret["nos"] = self.dg_nos_description
                ret["is_nos"] = is_nos

        if self.is_pharma:
            ret["is_time_sensitive"] = self.is_time_sensitive
            ret["is_cos"] = self.is_cos

            if self.is_time_sensitive:
                ret["time_sensitive_hours"] = self.time_sensitive_hours

        elif self.packing_type == "CONTAINER":
            ret["container_number"] = self.container_number
            ret["status"] = self.container_pack
        elif self.packing_type == "CONTAINER":
            ret["condition"] = self.vehicle_condition
            ret["anti_theft"] = self.anti_theft
            ret["year"] = self.year
            ret["model"] = self.make
            ret["vin"] = self.vin

        return ret

    # Override
    def clean(self) -> None:
        dg_fields = (self.un_number, self.packing_group, self.packing_type, self.dg_quantity)

        if any(dg_field is not None and dg_field != 0 for dg_field in dg_fields) is True:
            if any(dg_field is None or not dg_field for dg_field in dg_fields) is True:
                raise ValidationError("If any dangerous goods attributes are set all or none must be set.")

    # Override
    def save(self, *args, **kwargs):
        self.width = self.width.quantize(self._dim_sig_fig)
        self.length = self.length.quantize(self._dim_sig_fig)
        self.height = self.height.quantize(self._dim_sig_fig)
        self.weight = self.weight.quantize(self._weight_sig_fig)
        self.freight_class_id = self.freight_class_id.quantize(self._dim_sig_fig)

        self.clean_fields()
        self.clean()
        super().save()

    # Override
    def __repr__(self) -> str:
        return f"< Package ({self.package_id}: {self.length}x{self.width}x{self.height}, {self.weight}, " \
            f"{self.get_package_type_display()}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.package_id}: {self.length}x{self.width}x{self.height}, {self.weight}, " \
            f"{self.get_package_type_display()}"
