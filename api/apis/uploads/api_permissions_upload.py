"""
    Title: Api Permissions Upload
    Description: This file will contain all functions to upload Api Permissions.
    Created: February 16, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ValidationError

from api.exceptions.project import ViewException
from api.models import ApiPermissions


class ApiPermissionUpload:

    @staticmethod
    def process_workbook(workbook):
        """
            Process excel sheet and create new api permission records.
            :param workbook:
            :return:
        """
        errors = []
        rows = workbook.rows

        next(rows)
        for row in rows:

            if not row[0].value:
                break

            params = {
                "name": str(row[0].value).strip(),
                "permissions": str(row[1].value).strip(),
                "category": str(row[2].value).strip(),
                "active": str(row[4].value).strip() == "TRUE",
                "admin": str(row[5].value).strip() == "TRUE"
            }

            if str(row[3].value).strip() != "None":
                params["reason"] = str(row[3].value).strip()

            try:
                ApiPermissions.create(param_dict=params).save()
            except ValidationError as e:
                errors.extend([{x: y} for x, y in e.message_dict.items()])
                raise ViewException(code="7905", message="Api Permission: failed to save. (Upload)", errors=errors)

    def import_errors(self, workbook) -> None:
        """
            Import excel sheet of api permission into the system.
            :param workbook: Excel Sheet
        """
        self.process_workbook(workbook=workbook)

