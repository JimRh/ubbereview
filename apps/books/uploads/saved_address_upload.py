"""
    Title: Saved Address Upload
    Description: This file will contain all functions to upload saved addresses.
    Created: February 7, 2023
    Author: Yusuf
    Edited By:
    Edited Date:
"""

# TODO - Bulk Save address and saved address for efficiency?


from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from rest_framework import serializers

from api.models import Province, Address
from apps.books.models import SavedAddress
from apps.common.utilities.address import (
    clean_address,
    clean_city,
    clean_postal_code,
    hash_address,
)


class SavedAddressUpload:
    """
    Upload saved address excel rate sheet.
    """

    @staticmethod
    @transaction.atomic()
    def process_workbook(workbook, data):
        """
        Processes and creates all saved addresses from Excel sheet
        :param workbook:
        :param data:
        :return:
        """

        errors = dict()
        rows = list(workbook.rows)

        for i in range(1, len(rows)):
            name = rows[i][0].value
            province = rows[i][3].value
            country = rows[i][4].value
            is_residential = str(rows[i][6].value).strip().upper()
            is_origin = str(rows[i][7].value).strip().upper()
            is_destination = str(rows[i][8].value).strip().upper()

            address = {
                "address": clean_address(address=str(rows[i][1].value)),
                "province": str(province).strip(),
                "city": clean_city(city=str(rows[i][2].value).strip()),
                "postal_code": clean_postal_code(str(rows[i][5].value)),
                "has_shipping_bays": is_residential == "NO",
            }

            address_hash = hash_address(
                data={
                    "address": address["address"],
                    "city": address["city"],
                    "province": {
                        "code": address["province"],
                        "country": {
                            "code": country,
                        },
                    },
                    "postal_code": address["postal_code"],
                }
            )

            try:
                address["province"] = Province.objects.get(
                    code=province, country__code=country
                )
            except ObjectDoesNotExist as e:
                errors["province"] = [
                    f"Row: {i} - Not found with 'code': {province} and 'country code': {country}."
                ]
                raise serializers.ValidationError(errors)

            if is_residential not in ["YES", "NO"]:
                errors["residential"] = [
                    f"Row: {i} - Residential cell must be 'YES' or 'NO'."
                ]

            if is_origin not in ["YES", "NO"]:
                errors["origin"] = [f"Row: {i} - Origin cell must be 'YES' or 'NO'."]

            if is_destination not in ["YES", "NO"]:
                errors["destination"] = [
                    f"Row: {i} - Destination cell must be 'YES' or 'NO'."
                ]

            if SavedAddress.objects.filter(
                account=data["account"], address_hash=address_hash
            ).exists():
                errors["address"] = [f"Row: {i} - Saved Address already exists."]
                raise serializers.ValidationError(errors)

            if errors:
                raise serializers.ValidationError(errors)

            try:
                address = Address.create(param_dict=address)
                address.save()
            except ValidationError as e:
                errors.update(e.message_dict)
                raise serializers.ValidationError(errors)

            param_dict = {
                "account": data["account"],
                "address_hash": address_hash,
                "name": name,
                "username": data["username"],
                "address": address,
                "is_origin": is_origin == "YES",
                "is_destination": is_destination == "YES",
                "is_vendor": data["is_vendor"],
            }

            try:
                saved_address = SavedAddress.create(param_dict=param_dict)
                saved_address.save()
            except ValidationError as e:
                errors.update(e.message_dict)
                raise serializers.ValidationError(errors)

    def import_saved_address(self, workbook, data) -> None:
        """
        Imports saved addresses from excel sheet and passes in the users account number
        :param workbook:
        :param data:
        :return:
        """

        self.process_workbook(workbook=workbook, data=data)
