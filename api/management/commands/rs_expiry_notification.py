"""
    Title: Rate Sheet Notification System
    Description: This file will responsible for determining which rate sheets are expiring at 60, 30, 15 , and 5 days.
                 The result will send an email to the carrier manager email address.
    Created: October 27, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime
import io
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import xlsxwriter
from django.core.management import BaseCommand
from django.utils import timezone

from api.models import RateSheet
from brain.settings import LOGGER_FROM_EMAIL, EMAIL_HOST, EMAIL_PORT


class Command(BaseCommand):

    height = 2
    headings = [
        "Expiry Date",
        "Carrier",
        "Mode",
        "Service Name",
        "Service Code",
        "Origin City",
        "Origin Province",
        "Origin Country",
        "Destination City",
        "Destination Province",
        "Destination Country",
        "transit Days",
        "Cutoff Time",
        "Availability",
        "Flat Rate",
    ]

    def handle(self, *args, **options) -> None:

        expiring_lanes = {
            "expired": [],
            "five_days": [],
            "fifteen_days": [],
            "thirty_days": [],
            "sixty_days": [],
        }

        today = datetime.datetime.now().replace(tzinfo=timezone.utc)
        five_days = today + datetime.timedelta(days=5)
        fifteen_days = today + datetime.timedelta(days=15)
        thirty_days = today + datetime.timedelta(days=30)
        sixty_days = today + datetime.timedelta(days=60)

        expiring_lanes["expired"] = RateSheet.objects.filter(expiry_date__lt=today)
        expiring_lanes["five_days"] = RateSheet.objects.filter(expiry_date__range=[today, five_days])
        expiring_lanes["fifteen_days"] = RateSheet.objects.filter(expiry_date__range=[five_days, fifteen_days])
        expiring_lanes["thirty_days"] = RateSheet.objects.filter(expiry_date__range=[fifteen_days, thirty_days])
        expiring_lanes["sixty_days"] = RateSheet.objects.filter(expiry_date__range=[thirty_days, sixty_days])

        file_name = f"Expiring Rate Sheets {datetime.datetime.today().strftime('%Y-%m-%d')}.xlsx"
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        data = self._create_data(rate_sheets=expiring_lanes)

        for key, rs_list in data.items():
            worksheet = workbook.add_worksheet(name=key)

            self._init_style(workbook=workbook)
            self._create_header(worksheet=worksheet)
            start_row = 1

            for i in range(len(rs_list)):
                for j in range(len(rs_list[i])):
                    worksheet.write(i + start_row, j, rs_list[i][j])

        workbook.close()
        output.seek(0)

        smtp_server = smtplib.SMTP(
            host=EMAIL_HOST,
            port=EMAIL_PORT
        )

        try:
            smtp_server.starttls()
        except smtplib.SMTPNotSupportedError:
            pass

        smtp_server.ehlo_or_helo_if_needed()
        # smtp_server.login(EMAIL_HOST_USER, "")

        from_addr = LOGGER_FROM_EMAIL
        to_addr = "customerservice@ubbe.com"

        msg = MIMEMultipart()
        msg['From'] = from_addr
        msg['To'] = to_addr
        msg['Subject'] = "Expiring Rate Sheets"

        msg.attach(MIMEText(file_name, 'plain'))
        part = MIMEBase('application', 'octet-stream')

        part.set_payload(output.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % file_name)
        msg.attach(part)
        smtp_server.sendmail(from_addr, to_addr, msg.as_string())
        smtp_server.quit()

    @staticmethod
    def data_array(sheet: RateSheet) -> list:
        """
            Create Rate Sheet data array for excel row.
            :param sheet: Rate Sheet
            :return: list
        """
        return [
            sheet.expiry_date.strftime('%Y-%m-%d'),
            sheet.carrier.name,
            sheet.carrier.get_mode_display(),
            sheet.service_name,
            sheet.service_code,
            sheet.origin_city,
            sheet.origin_province.code,
            sheet.origin_province.country.code,
            sheet.destination_city,
            sheet.destination_province.code,
            sheet.destination_province.country.code,
            sheet.transit_days,
            sheet.cut_off_time,
            sheet.availability,
            sheet.get_rs_type_display(),
        ]

    def _create_data(self, rate_sheets: dict) -> dict:
        """
            Create shipment data lists after getting queried data from the db
            :return: list
        """
        final_data = {}

        for key, rs_list in rate_sheets.items():
            data = []

            for lane in rs_list:
                data.append(self.data_array(sheet=lane))

                self.height += 1

            final_data[key] = data

        return final_data

    def _create_header(self, worksheet) -> None:
        """
            Create excel header row.
        """
        for i in range(len(self.headings)):
            worksheet.write(0, i, self.headings[i], self.header_right)

    def _init_style(self, workbook) -> None:
        """
            Create excel styles for rows.
        """
        self.border_center_bold = workbook.add_format({'border': 1, 'align': 'center', 'bold': True})
        self.right = workbook.add_format({'right': 2})
        self.header = workbook.add_format({'top': 2, 'bottom': 2, 'bold': True})
        self.header_right = workbook.add_format({'top': 2,  'bottom': 2, 'right': 2, 'bold': True})
