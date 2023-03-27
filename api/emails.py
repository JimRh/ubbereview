import copy
import datetime
import os
from decimal import Decimal
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage

import html2text
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string

from api.globals.project import DOCUMENT_TYPE_SHIPPING_LABEL
from brain.settings import SHIPMENT_REQUEST_EMAIL, BASE_DIR, SKYLINE_PICKUP_REQUEST_EMAIL, \
    PICKUP_REQUEST_EMAIL, LOGGER_FROM_EMAIL, DEBUG


class Emails:

    @staticmethod
    def rate_sheet_email(gobox_request: dict):

        if 'sub' in gobox_request:
            sub = gobox_request["sub"]
        else:
            sub = "Shipment"

        if gobox_request.get("is_bbe", False):
            request_email = gobox_request.get("email", SHIPMENT_REQUEST_EMAIL)
        else:
            request_email = SHIPMENT_REQUEST_EMAIL

        gobox_request["reply_to"] = request_email

        recipients = [gobox_request["carrier_email"], request_email, gobox_request['api_client_email']]
        subject = 'ubbe {} Request: {}'.format(sub, gobox_request["order_number"])

        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_tables = True
        html_message = render_to_string('manual_email/send_shipment.html', gobox_request)

        msg = EmailMultiAlternatives(
            subject,
            html_message,
            LOGGER_FROM_EMAIL,
            recipients,
            reply_to=[LOGGER_FROM_EMAIL]
        )

        msg.content_subtype = 'html'
        msg.mixed_subtype = 'related'

        for f in ['Horiz_Ubbe_Logo_Flat_Colour.png', 'sm-facebook.png', 'sm-twitter.png']:
            fp = open(os.path.join(os.path.join(BASE_DIR, 'api/static/img/'), f), 'rb')
            msg_img = MIMEImage(fp.read())
            fp.close()
            msg_img.add_header('Content-ID', '<{}>'.format(f))
            msg.attach(msg_img)

        response = msg.send()

        return response

    @staticmethod
    def bbe_email(gobox_request: dict, files: list):

        if 'sub' in gobox_request:
            sub = gobox_request["sub"]
        else:
            sub = "Shipment"

        recipients = [gobox_request["carrier_email"], SHIPMENT_REQUEST_EMAIL, gobox_request['api_client_email']]
        subject = 'ubbe {} Request: {}'.format(sub, gobox_request["order_number"])
        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_tables = True
        html_message = render_to_string('manual_email/send_shipment.html', gobox_request)

        msg = EmailMultiAlternatives(
            subject,
            html_message,
            LOGGER_FROM_EMAIL,
            recipients,
            reply_to=[LOGGER_FROM_EMAIL]
        )

        msg.content_subtype = 'html'
        msg.mixed_subtype = 'related'

        for f in ['Horiz_Ubbe_Logo_Flat_Colour.png', 'sm-facebook.png', 'sm-twitter.png']:
            fp = open(os.path.join(os.path.join(BASE_DIR, 'api/static/img/'), f), 'rb')
            msg_img = MIMEImage(fp.read())
            fp.close()
            msg_img.add_header('Content-ID', '<{}>'.format(f))
            msg.attach(msg_img)

        for file in files:

            if file["type"] == DOCUMENT_TYPE_SHIPPING_LABEL:
                file_name = f'{gobox_request["order_number"]}-Cargo-Label.pdf'
            else:
                file_name = f'{gobox_request["order_number"]}-BOL.pdf'

            pdf = MIMEBase('application', 'octet-stream')
            pdf.set_payload(file["document"])
            pdf.add_header('Content-Transfer-Encoding', 'base64')
            pdf['Content-Disposition'] = 'attachment; filename="%s"' % file_name
            msg.attach(pdf)

        response = msg.send()

        return response

    @staticmethod
    def mlcarrier_email(gobox_request: dict, files: list, ship_data: dict):
        if 'sub' in gobox_request:
            sub = gobox_request["sub"]
        else:
            sub = "Shipment"

        recipients = [SHIPMENT_REQUEST_EMAIL, gobox_request['api_client_email']]
        subject = 'MACHINE LEARNING: ubbe {} Request: {}'.format(sub, gobox_request["order_number"])
        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_tables = True
        gobox_request["ship_data"] = ship_data
        html_message = render_to_string('manual_email/ml_carrier_shipment.html', gobox_request)

        msg = EmailMultiAlternatives(
            subject,
            html_message,
            LOGGER_FROM_EMAIL,
            recipients,
            reply_to=[LOGGER_FROM_EMAIL],
            headers={"Priority": "Urgent", "Importance": "high"}
        )

        msg.content_subtype = 'html'
        msg.mixed_subtype = 'related'

        for f in ['Horiz_Ubbe_Logo_Flat_Colour.png', 'sm-facebook.png', 'sm-twitter.png']:
            fp = open(os.path.join(os.path.join(BASE_DIR, 'api/static/img/'), f), 'rb')
            msg_img = MIMEImage(fp.read())
            fp.close()
            msg_img.add_header('Content-ID', '<{}>'.format(f))
            msg.attach(msg_img)

        for file in files:
            if file["type"] == DOCUMENT_TYPE_SHIPPING_LABEL:
                file_name = f'{gobox_request["order_number"]}-Cargo-Label.pdf'
            else:
                file_name = f'{gobox_request["order_number"]}-BOL.pdf'

            pdf = MIMEBase('application', 'octet-stream')
            pdf.set_payload(file["document"])
            pdf.add_header('Content-Transfer-Encoding', 'base64')
            pdf['Content-Disposition'] = 'attachment; filename="%s"' % file_name
            msg.attach(pdf)

        response = msg.send()

        return response

    @staticmethod
    def skyline_pd_email(context: dict):

        recipient_list = [SKYLINE_PICKUP_REQUEST_EMAIL]

        if context["is_pickup"]:
            subject = 'ubbe: {} - {} Community Pickup'.format(context["order_number"], context.get("city"))
        else:
            subject = 'ubbe: {} - {} Community Delivery'.format(context["order_number"], context.get("city"))

        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_tables = True
        html_message = render_to_string('skyline/pickup_notification.html', context)

        response = send_mail(
            subject=subject,
            recipient_list=recipient_list,
            from_email=LOGGER_FROM_EMAIL,
            html_message=html_message,
            message=html_message,
            fail_silently=False
        )

        return response

    @staticmethod
    def pickup_issue_email(data: dict, carrier: str, order_number: str, pickup_data: dict, is_fail: bool):
        context = copy.deepcopy(data)

        if is_fail:
            subject = carrier.title() + " Pickup Booking Modified Time Notification"
        else:
            subject = carrier.title() + " Pickup Booking Failure"

        total_packages = 0
        total_weight = Decimal("0.00")
        weight_unit = "kg" if data.get('is_metric', True) else "lbs"
        awb_message = ''

        for package in data["packages"]:
            total_packages += 1
            total_weight += Decimal(str(package["weight"]))

        if data.get("awb", ''):
            awb_message = "Please attach AWB " + data["awb"] + " as a reference number\n\n"

        context.update({
            "carrier_name": carrier,
            "order_number": order_number,
            "is_fail": is_fail,
            "weight_unit": weight_unit,
            "total_packages": total_packages,
            "total_weight": total_weight,
            "awb_message": awb_message
        })

        context.update(pickup_data)

        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_tables = True
        html_message = render_to_string('pickup_issue.html', context)

        response = send_mail(
            subject=subject,
            recipient_list=[PICKUP_REQUEST_EMAIL],
            from_email=LOGGER_FROM_EMAIL,
            html_message=html_message,
            message=html_message,
            fail_silently=False
        )

        return response

    @staticmethod
    def interline_email(context: dict, email: str):
        """
            Send Email Notification
            :param context: Data to send in email.
            :param email: email to send to.
            :return:
        """

        recipient_list = [email, "developer@bbex.com"]

        subject = f'ubbe Interline Notification: {context["shipment_id"]}'

        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_tables = True
        html_message = render_to_string('interlines_note.html', context)

        response = send_mail(
            subject=subject,
            recipient_list=recipient_list,
            from_email=LOGGER_FROM_EMAIL,
            html_message=html_message,
            message=html_message,
            fail_silently=False,
        )

        return response

    @staticmethod
    def low_airwaybill_email(data: dict):
        """
            Send Email Notification
            :param data: Data to send in email.
            :param email: email to send to.
            :return:
        """

        if DEBUG:
            recipient_list = ["developer@bbex.com"]
        else:
            recipient_list = ["customerservice@ubbe.com"]

        subject = f'ubbe Low Airwaybill Notification'

        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_tables = True
        html_message = render_to_string('low_airwaybill.html', data)

        response = send_mail(
            subject=subject,
            recipient_list=recipient_list,
            from_email=LOGGER_FROM_EMAIL,
            html_message=html_message,
            message=html_message,
            fail_silently=False,
        )

        return response

    @staticmethod
    def overdue_email(context: dict):
        """
            Send overdue Notification
            :param context: Data to send in email.
            :param email: email to send to.
            :return:
        """

        if DEBUG:
            recipient_list = ["developer@bbex.com"]
        else:
            recipient_list = ["customerservice@ubbe.com"]

        subject = f'ubbe Overdue Alert'

        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_tables = True
        html_message = render_to_string('overdue_alert.html', context)

        response = send_mail(
            subject=subject,
            recipient_list=recipient_list,
            from_email=LOGGER_FROM_EMAIL,
            html_message=html_message,
            message=html_message,
            fail_silently=False,
        )

        return response

    @staticmethod
    def confirmation_email(data: dict, email: str):

        if DEBUG:
            recipient_list = ['developer@bbex.com']
        else:
            recipient_list = [email]

        subject = f'ubbe Shipment Confirmation: {data["shipment_id"]}'

        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_tables = True
        html_message = render_to_string('confirmation_email.html', data)

        msg = EmailMultiAlternatives(
            subject, html_message, LOGGER_FROM_EMAIL, recipient_list, reply_to=[LOGGER_FROM_EMAIL]
        )

        msg.content_subtype = 'html'
        msg.mixed_subtype = 'related'

        for f in ['chat.png', 'phone.png', 'web.png', 'hex.png', 'hexSmall.png', 'Logo-H-Col.png',
                  'Horiz_Ubbe_Logo_Flat_Colour.png', 'BBEw200h160.png', 'sm-facebook.png', 'sm-twitter.png']:
            fp = open(os.path.join(os.path.join(BASE_DIR, 'api/static/img/'), f), 'rb')
            msg_img = MIMEImage(fp.read())
            fp.close()
            msg_img.add_header('Content-ID', '<{}>'.format(f))
            msg.attach(msg_img)

        response = msg.send()

        return response

    @staticmethod
    def insurance_email(data: dict):

        if DEBUG:
            recipient_list = ['developer@bbex.com']
        else:
            recipient_list = ['customerservice@ubbe.com']

        subject = f'ubbe Shipment Insurance: {data["shipment_id"]}'

        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_tables = True
        html_message = render_to_string('insurance_email.html', data)

        msg = EmailMultiAlternatives(
            subject, html_message, LOGGER_FROM_EMAIL, recipient_list, reply_to=[LOGGER_FROM_EMAIL]
        )

        msg.content_subtype = 'html'
        msg.mixed_subtype = 'related'

        for f in ['chat.png', 'phone.png', 'web.png', 'hex.png', 'hexSmall.png', 'Logo-H-Col.png',
                  'Horiz_Ubbe_Logo_Flat_Colour.png', 'BBE_GoBox_Logo_FullColour_RGB.png']:
            fp = open(os.path.join(os.path.join(BASE_DIR, 'api/static/img/'), f), 'rb')
            msg_img = MIMEImage(fp.read())
            fp.close()
            msg_img.add_header('Content-ID', '<{}>'.format(f))
            msg.attach(msg_img)

        response = msg.send()

        return response

    @staticmethod
    def cancel_shipment_email(context: dict):
        if DEBUG:
            recipient_list = ["developer@bbex.com"]
        else:
            recipient_list = ["customerservice@ubbe.com"]
        subject = 'ubbe Cancel Shipment: {}'.format(context["shipment_id"])

        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_tables = True
        html_message = render_to_string('cancel_shipment.html', context)

        msg = EmailMultiAlternatives(
            subject, html_message, LOGGER_FROM_EMAIL, recipient_list, reply_to=[LOGGER_FROM_EMAIL]
        )

        msg.content_subtype = 'html'
        msg.mixed_subtype = 'related'

        for f in ['chat.png', 'phone.png', 'web.png', 'hex.png', 'hexSmall.png', 'Logo-H-Col.png',
                  'Horiz_Ubbe_Logo_Flat_Colour.png', 'BBE_GoBox_Logo_FullColour_RGB.png']:
            fp = open(os.path.join(os.path.join(BASE_DIR, 'api/static/img/'), f), 'rb')
            msg_img = MIMEImage(fp.read())
            fp.close()
            msg_img.add_header('Content-ID', '<{}>'.format(f))
            msg.attach(msg_img)

        response = msg.send()

        return response

    @staticmethod
    def cancel_pickup_email(context: dict):
        if DEBUG:
            recipient_list = ["developer@bbex.com"]
        else:
            recipient_list = ["customerservice@ubbe.com"]
        subject = 'ubbe Cancel Pickup: {}'.format(context["leg_id"])

        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_tables = True
        html_message = render_to_string('cancel_pickup.html', context)

        msg = EmailMultiAlternatives(
            subject, html_message, LOGGER_FROM_EMAIL, recipient_list, reply_to=[LOGGER_FROM_EMAIL]
        )

        msg.content_subtype = 'html'
        msg.mixed_subtype = 'related'

        for f in ['chat.png', 'phone.png', 'web.png', 'hex.png', 'hexSmall.png', 'Logo-H-Col.png',
                  'Horiz_Ubbe_Logo_Flat_Colour.png', 'BBE_GoBox_Logo_FullColour_RGB.png']:
            fp = open(os.path.join(os.path.join(BASE_DIR, 'api/static/img/'), f), 'rb')
            msg_img = MIMEImage(fp.read())
            fp.close()
            msg_img.add_header('Content-ID', '<{}>'.format(f))
            msg.attach(msg_img)

        response = msg.send()

        return response

    @staticmethod
    def receipt_email(data: dict, files: list):

        recipients = [data["email"]]
        subject = f'ubbe Receipt for {data["shipment_id"]}'

        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_tables = True
        html_message = render_to_string('receipt_email.html', data)

        msg = EmailMultiAlternatives(
            subject,
            html_message,
            LOGGER_FROM_EMAIL,
            recipients,
            reply_to=[LOGGER_FROM_EMAIL]
        )

        msg.content_subtype = 'html'
        msg.mixed_subtype = 'related'

        for f in ['Horiz_Ubbe_Logo_Flat_Colour.png', 'sm-facebook.png', 'sm-twitter.png']:
            fp = open(os.path.join(os.path.join(BASE_DIR, 'api/static/img/'), f), 'rb')
            msg_img = MIMEImage(fp.read())
            fp.close()
            msg_img.add_header('Content-ID', '<{}>'.format(f))
            msg.attach(msg_img)

        for file in files:
            file_name = f'{data["shipment_id"]}-receipt.pdf'
            pdf = MIMEBase('application', 'octet-stream')
            pdf.set_payload(file)
            pdf.add_header('Content-Transfer-Encoding', 'base64')
            pdf['Content-Disposition'] = 'attachment; filename="%s"' % file_name
            msg.attach(pdf)

        response = msg.send()

        return response
