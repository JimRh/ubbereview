"""
    Title: Error Code Upload
    Description: This file will contain all functions to upload error codes.
    Created: February 9, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ValidationError

from api.exceptions.project import ViewException
from api.models import ErrorCode


class ErrorCodeUpload:

    @staticmethod
    def process_workbook(workbook):
        """
            Process excel sheet and create new error code records.
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
                    "system": str(row[0].value).strip(),
                    "source": str(row[1].value).strip(),
                    "type": str(row[2].value).strip(),
                    "code": str(row[3].value).strip(),
                    "name": str(row[4].value).strip(),
                    "actual_message": str(row[5].value).strip()
                }

            if str(row[6].value).strip() != "None":
                params["solution"] = str(row[6].value).strip()

            if str(row[7].value).strip() != "None":
                params["location"] = str(row[7].value).strip()

            try:
                ErrorCode.create(param_dict=params).save()
            except ValidationError as e:
                errors.extend([{x: y} for x, y in e.message_dict.items()])
                raise ViewException(code="4510", message="Error Codes: failed to save. (Upload)", errors=errors)

    def import_errors(self, workbook) -> None:
        """
            Import excel sheet of error codes into the system.
            :param workbook: Excel Sheet
        """
        self.process_workbook(workbook=workbook)

