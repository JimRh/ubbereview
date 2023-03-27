"""
    Title: Saved Package Upload
    Description: This file will contain all functions to upload city aliases.
    Created: October 27, 2022
    Author: Yusuf
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist, ValidationError

from api.exceptions.project import ViewException
from api.models import SubAccount, SavedPackage


class SavedPackageUpload:
    """
        Upload saved package excel rate sheet.
    """

    @staticmethod
    def get_subaccount(account_number: str):
        """
           Gets the users subaccount
           :param account_number:
           :return: sub_account
        """
        try:
            sub_account = SubAccount.objects.get(subaccount_number=account_number)
        except ObjectDoesNotExist as e:
            raise ViewException(code="1209", message="Saved Package: Sub Account not found.", errors=[])
        return sub_account

    @staticmethod
    def process_workbook(workbook, sub_account, box_type):
        """
            Proccesses and creates all packages from excel sheet
            :param workbook:
            :param sub_account:
            :return:
        """

        rows = list(workbook.rows)

        for i in range(1, len(rows)):
            package_type = rows[i][0].value
            freight_class_id = rows[i][1].value
            description = rows[i][2].value
            length = rows[i][3].value
            width = rows[i][4].value
            height = rows[i][5].value
            weight = rows[i][6].value

            if not freight_class_id:
                freight_class_id = Decimal("-1.00")

            param_dict = {
                "sub_account": sub_account,
                "box_type": box_type,
                "package_type": package_type,
                "freight_class_id": freight_class_id,
                "description": str(description).lower().strip(),
                "length": length,
                "width": width,
                "height": height,
                "weight": weight,
            }

            try:
                package = SavedPackage.create(param_dict=param_dict)
                package.save()

            except ValidationError as e:
                raise ViewException(f"Saved Package Creation error: {str(e)}.")

    def import_saved_package(self, workbook, account_number, box_type) -> None:
        """
            Imports saved packages from excel sheet and passes in the users account number.
            :param workbook:
            :param account_number:
            :return:
        """
        sub_account = self.get_subaccount(account_number=account_number["subaccount_number"])
        self.process_workbook(workbook=workbook, sub_account=sub_account, box_type=box_type)
