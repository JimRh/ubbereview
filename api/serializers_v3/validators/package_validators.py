"""
    Title: Package Validators
    Description: This file will contain functions for package validating.
    Created: November 29, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from rest_framework import serializers

from api.models import DangerousGood


class PackageSkidValidator:

    def __init__(self, phone: str):
        self.phone = phone

    def valid(self) -> str:
        phone = self.phone.strip()

        if not phone.isdigit():
            raise serializers.ValidationError({'phone': [f'This field mush be numbers only.']})

        return phone


class PackageDGValidator:

    def __init__(self, data: dict):
        self.data = data

    def valid(self) -> None:
        """
            Ensure all required dg fields are included in request.
        """
        message_required = f"This field is required."

        exists = DangerousGood.objects.filter(
            un_number=self.data["un_number"],
            packing_group__packing_group=self.data["packing_group"],
            short_proper_shipping_name=self.data["proper_shipping_name"]
        )

        if not exists:
            message = f"The combination of 'un_number': '{self.data['un_number']}', " \
                f"'proper_shipping_name': '{self.data['proper_shipping_name']}', " \
                f"'packing_group': '{self.data['packing_group']}' does not exist."
            raise serializers.ValidationError({'un_number': [message]})

        if not self.data.get("packing_type"):
            raise serializers.ValidationError({'packing_type': [message_required]})

        if not self.data.get("dg_quantity"):
            raise serializers.ValidationError({'dg_quantity': [message_required]})

        if self.data.get("is_dg_nos"):

            if not self.data.get("dg_nos_description"):
                raise serializers.ValidationError({'dg_nos_description': [message_required]})


class PackageVehicleValidator:

    def __init__(self, phone: str):
        self.phone = phone

    def valid(self) -> str:
        phone = self.phone.strip()

        if not phone.isdigit():
            raise serializers.ValidationError({'phone': [f'This field mush be numbers only.']})

        return phone
