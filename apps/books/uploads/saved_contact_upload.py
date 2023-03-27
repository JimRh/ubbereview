"""
    Title: Saved Contact Upload
    Description: This file will contain all functions to upload saved Contacts.
    Created: February 7, 2023
    Author: Yusuf
    Edited By:
    Edited Date:
"""

# TODO - Bulk Save Contact and saved contact for efficiency?


from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import serializers

from api.models import Contact
from apps.books.models import SavedContact
from apps.common.utilities.contact import hash_contact


class SavedContactUpload:
    """
    Upload saved contact excel rate sheet.
    """
    @staticmethod
    @transaction.atomic
    def process_workbook(workbook, data):
        """
        Processes and creates all saved contacts from Excel sheet
        :param workbook:
        :param data:
        :return:
        """

        errors = dict()
        rows = list(workbook.rows)

        for i in range(1, len(rows)):
            company_name = rows[i][0].value
            name = rows[i][1].value
            phone = rows[i][2].value
            extension = rows[i][3].value
            email = rows[i][4].value
            is_origin = rows[i][5].value
            is_destination = rows[i][6].value

            contact = {
                "company_name": str(company_name).strip(),
                "name": str(name).strip(),
                "phone": str(phone).strip(),
                "extension": str(extension).strip(),
                "email": str(email).strip()
            }

            contact_hash = hash_contact(data=contact)

            if is_origin not in ["YES", "NO"]:
                errors["origin"] = [f"Row: {i} - Origin cell must be 'YES' or 'NO'."]

            if is_destination not in ["YES", "NO"]:
                errors["destination"] = [
                    f"Row: {i} - Destination cell must be 'YES' or 'NO'."
                ]

            if SavedContact.objects.filter(
                account=data["account"], contact_hash=contact_hash
            ).exists():
                errors["contact"] = [f"Row: {i} - Saved Contact already exists."]
                raise serializers.ValidationError(errors)

            if errors:
                raise serializers.ValidationError(errors)

            try:
                contact = Contact.create(param_dict=contact)
                contact.save()
            except ValidationError as e:
                errors.update(e.message_dict)
                raise serializers.ValidationError(errors)

            param_dict = {
                "account": data["account"],
                "contact_hash": contact_hash,
                "name": name,
                "username": data["username"],
                "contact": contact,
                "is_origin": is_origin == "YES",
                "is_destination": is_destination == "YES",
                "is_vendor": data["is_vendor"],
            }

            try:
                saved_contact = SavedContact.create(param_dict=param_dict)
                saved_contact.save()
            except ValidationError as e:
                errors.update(e.message_dict)
                raise serializers.ValidationError(errors)

    def import_saved_contact(self, workbook, data) -> None:
        """
        Imports saved contacts from excel sheet and passes in the users account number
        :param workbook:
        :param data:
        :return:
        """

        self.process_workbook(workbook=workbook, data=data)
