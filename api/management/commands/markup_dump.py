import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.core.management import BaseCommand
import xlsxwriter
from api.models import Markup
from brain.settings import LOGGER_FROM_EMAIL, EMAIL_HOST, EMAIL_PORT


class Command(BaseCommand):

    def handle(self, *args, **options) -> None:

        markups = Markup.objects.prefetch_related("carrier_markup_markup__carrier").all()
        markup_list = [
            [
                "Markup",
                "Description",
                "Percentage",
                "Default Carrier Percentage",
                "Carrier",
                "Carrier Percentage",
            ]
        ]

        for markup in markups:

            for carrier in markup.carrier_markup_markup.all():
                markup_list.append([
                    markup.name,
                    markup.description,
                    markup.default_percentage,
                    markup.default_carrier_percentage,
                    carrier.carrier.name,
                    carrier.percentage
                ])

        # print(markup_list)

        filename = "markups.xlsx"
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()

        # Iterate over the data and write it out row by row.
        for i in range(len(markup_list)):
            for j in range(len(markup_list[i])):
                worksheet.write(i, j, markup_list[i][j])

        workbook.close()

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
        to_addr = "developer@bbex.com"

        msg = MIMEMultipart()
        msg['From'] = from_addr
        msg['To'] = to_addr
        msg['Subject'] = "GoBox Shipment Report"

        msg.attach(MIMEText("GoBox Shipment Report", 'plain'))

        attachment = open(filename, 'rb')
        part = MIMEBase('application', 'octet-stream')

        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
        msg.attach(part)
        smtp_server.sendmail(from_addr, to_addr, msg.as_string())
        smtp_server.quit()
