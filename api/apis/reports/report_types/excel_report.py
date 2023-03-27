"""
    Title: Excel Report
    Description: This file will contain class of functions to create a excel report from passed in data.
    Created: April  26, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import base64
import io

import xlsxwriter

from api.globals.project import LOGGER


class ExcelReport:

    def __init__(self, data: list, headings: list):

        self.height = 2
        self._data = data
        self._headings = headings

    def _init_style(self, workbook) -> None:
        """
            Create excel styles for rows.
        """
        self.border_center_bold = workbook.add_format({'border': 1, 'align': 'center', 'bold': True})
        self.right = workbook.add_format({'right': 2})
        self.header = workbook.add_format({'top': 2, 'bottom': 2, 'bold': True})
        self.header_right = workbook.add_format({'top': 2,  'bottom': 2, 'right': 2, 'bold': True})
        self.top = workbook.add_format({'top': 1})

        self.bg_green = workbook.add_format()
        self.bg_green.set_bg_color('green')

        self.bg_green_border = workbook.add_format({'top': 1})
        self.bg_green_border.set_bg_color('green')

        self.bg_yellow = workbook.add_format()
        self.bg_yellow.set_bg_color('yellow')

        self.bg_yellow_border = workbook.add_format({'top': 1})
        self.bg_yellow_border.set_bg_color('yellow')

        self.bg_red = workbook.add_format()
        self.bg_red.set_bg_color('red')

        self.bg_red_border = workbook.add_format({'top': 1})
        self.bg_red_border.set_bg_color('red')

    def _create_header(self, worksheet) -> None:
        """
            Create excel header row.
        """
        for i in range(len(self._headings)):
            worksheet.write(0, i, self._headings[i], self.header_right)

    def _create_data_section(self, worksheet):
        """
            Create excel data section for the data.
            :return:
        """
        start_row = 1

        # Iterate over the data and write it out row by row.
        for i in range(len(self._data)):
            for j in range(len(self._data[i])):
                worksheet.write(i + start_row, j, self._data[i][j])

    def _create_data_section_tracking_leg(self, worksheet):
        """
            Create excel data section for the data.
            :return:
        """
        start_row = 1
        previous_shipment = None

        # Iterate over the data and write it out row by row.
        for i in range(len(self._data)):

            if i != 0:
                previous_shipment = self._data[i - 1][2]

            is_same = previous_shipment == self._data[i][2]

            for j in range(len(self._data[i])):

                if j == 20 and self._data[i][j] in ["DL", "dl", "P", "Delivered", "F", "DELIVERED", "Delivery"]:

                    if is_same:
                        worksheet.write(i + start_row, j, self._data[i][j], self.bg_green)
                    else:
                        worksheet.write(i + start_row, j, self._data[i][j], self.bg_green_border)

                    continue
                elif j == 20:

                    if is_same:
                        worksheet.write(i + start_row, j, self._data[i][j], self.bg_yellow)
                    else:
                        worksheet.write(i + start_row, j, self._data[i][j], self.bg_yellow_border)
                    continue

                if (j == 17 or j == 22) and self._data[i][j] == "Overdue":
                    if is_same:
                        worksheet.write(i + start_row, j, self._data[i][j], self.bg_red)
                    else:
                        worksheet.write(i + start_row, j, self._data[i][j], self.bg_red_border)
                    continue
                elif (j == 17 or j == 22) and self._data[i][j] == "Completed":
                    if is_same:
                        worksheet.write(i + start_row, j, self._data[i][j], self.bg_green)
                    else:
                        worksheet.write(i + start_row, j, self._data[i][j], self.bg_green_border)
                    continue
                elif (j == 17 or j == 22) and self._data[i][j] == "In Progress":
                    if is_same:
                        worksheet.write(i + start_row, j, self._data[i][j], self.bg_yellow)
                    else:
                        worksheet.write(i + start_row, j, self._data[i][j], self.bg_yellow_border)
                    continue

                if is_same:
                    worksheet.write(i + start_row, j, self._data[i][j])
                else:
                    worksheet.write(i + start_row, j, self._data[i][j], self.top)

    def create_report(self, is_tracking_leg: bool = False):
        """
            Create excel report for headers and data
            :return:
        """

        # if len(self._headings) != len(self._data[0]):
        #     raise Exception(f"Excel Report: Headers ({len(self._headings)}) must equal data ({len(self._data[0])}).")

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        self._init_style(workbook=workbook)
        self._create_header(worksheet=worksheet)

        if is_tracking_leg:
            self._create_data_section_tracking_leg(worksheet=worksheet)
        else:
            self._create_data_section(worksheet=worksheet)

        workbook.close()
        output.seek(0)

        return base64.b64encode(output.getvalue()).decode()
