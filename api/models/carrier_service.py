"""
    Title: CarrierService Model
    Description: This file will contain functions for CarrierService Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.deletion import PROTECT
from django.db.models.fields import CharField, BooleanField
from django.db.models.fields.related import ForeignKey

from api.globals.project import DEFAULT_CHAR_LEN, MAX_CHAR_LEN
from api.models import Carrier
from api.models.base_table import BaseTable


class CarrierService(BaseTable):
    """
        CarrierService Model
    """

    carrier = ForeignKey(Carrier, on_delete=PROTECT, related_name="carrierservice_carrier")
    name = CharField(max_length=DEFAULT_CHAR_LEN)
    code = CharField(max_length=DEFAULT_CHAR_LEN)
    description = CharField(max_length=MAX_CHAR_LEN)
    exceptions = CharField(max_length=MAX_CHAR_LEN, blank=True)
    service_days = CharField(
        max_length=DEFAULT_CHAR_LEN, default="Monday to Friday", help_text="Days the shipment will move"
    )
    is_international = BooleanField(default=False)

    class Meta:
        verbose_name = "Carrier Service"
        verbose_name_plural = "Carrier - Carrier Services"
        ordering = ["carrier__name", "name"]
        unique_together = ("carrier", "name")

    @staticmethod
    def get_service_information(carriers: list):
        """
            The function will grab all carrier service information for the passed in carriers
            :param carriers: list of carrier codes.
            :return: dictionary of carrier service information
        """

        ret = {}
        services = CarrierService.objects.select_related("carrier").all()

        for carrier_id, service_code in carriers:

            try:
                service_object = services.get(carrier__code=carrier_id, code=service_code)
            except ObjectDoesNotExist:
                continue

            if str(carrier_id) not in ret:
                ret[str(carrier_id)] = {}

            ret[str(carrier_id)][service_code] = {
                "service_name": service_object.name,
                "description": service_object.description,
                "exceptions": service_object.exceptions,
                "service_days": service_object.service_days
            }

        return ret

    # Override
    def __repr__(self) -> str:
        return f"< CarrierService ({self.name}, {self.description}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.name}, {self.description}"
