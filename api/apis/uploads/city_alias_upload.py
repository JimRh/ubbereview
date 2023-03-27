"""
    Title: City Alias Upload
    Description: This file will contain all functions to upload city aliases.
    Created: December 24, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from api.exceptions.project import ViewException
from api.models import Carrier, CityNameAlias, Province


class CityAliasUpload:

    @staticmethod
    def get_carrier(carrier_id: int):
        """
            Get Carrier Id
            :param carrier_id: Carrier id.
            :return:
        """

        try:
            carrier = Carrier.objects.get(code=carrier_id)
        except ObjectDoesNotExist:
            raise ViewException(f"Carrier with {carrier_id} does not exist.")

        return carrier

    @staticmethod
    def get_province(row, index_one, index_two, p_type):

        try:
            province = Province.objects.get(code=row[index_one].value, country__code=row[index_two].value)
        except ObjectDoesNotExist:
            raise ViewException(
                f"{p_type} province with code '{row[index_one].value}' and country code '{row[index_two].value}' could not be found"
            )

        return province

    def process_workbook(self, workbook, carrier: Carrier):
        """

            :param workbook:
            :param carrier:
            :return:
        """
        found_provinces = {}

        rows = workbook.rows

        next(rows)
        for row in rows:

            if not row[0].value:
                break

            origin = f"{row[2].value}{row[1].value}"

            if origin in found_provinces:
                city_province = found_provinces[origin]
            else:
                city_province = self.get_province(row=row, index_one=1, index_two=2, p_type="Origin")
                found_provinces[origin] = city_province

            try:
                alias = CityNameAlias.create(param_dict={
                    "name": str(row[0].value).strip().lower(),
                    "alias": str(row[3].value).strip().lower()
                })
                alias.carrier = carrier
                alias.province = city_province
                alias.save()
            except ValidationError as e:
                raise ViewException(f"City Alias Creation error: {str(e)}.")

    def import_city_alias(self, workbook, carrier_id: int) -> None:
        """

            :param workbook:
            :param carrier_id:
            :return:
        """

        carrier = self.get_carrier(carrier_id=carrier_id)
        self.process_workbook(workbook=workbook, carrier=carrier)

