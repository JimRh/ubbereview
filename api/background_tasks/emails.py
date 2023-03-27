"""
    Title: Celery Emails
    Description: This file will contain functions for Celery Emails.
    Created: May 5, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal
from smtplib import SMTPDataError
from time import sleep

from api.emails import Emails
from api.globals.project import LOGGER
from brain.celery import app


class CeleryEmail:
    """
        Send emails behind the scenes.
    """

    @app.task(bind=True)
    def rate_sheet_email(self, gobox_request: dict):
        """
            Send shipment request to rate sheet carrier
            :param gobox_request: shipment request
            :return: None
        """

        # Attempt to send request email
        try:
            response = Emails.rate_sheet_email(gobox_request=gobox_request)
        except SMTPDataError as e:
            LOGGER.critical("RateSheet email did not send first attempt.")
            response = -1
            max_attempts = 10
            count = 0

            # Attempt to send email again, with max retries of 10.
            while response == -1 and count <= max_attempts:

                sleep(3)

                try:
                    response = Emails.rate_sheet_email(gobox_request=gobox_request)
                except SMTPDataError as e:
                    continue

                if response != -1:
                    break

                count += 1

            if count == max_attempts:
                LOGGER.critical('RateSheet email exceeded max attempts: {}'.format(gobox_request))

    @app.task(bind=True)
    def bbe_email(self, gobox_request: dict, files: list):
        """
            Send shipment request to rate sheet carrier
            :param files:
            :param gobox_request: shipment request
            :return: None
        """

        # Attempt to send request email
        try:
            response = Emails.bbe_email(gobox_request=gobox_request, files=files)
        except SMTPDataError as e:
            LOGGER.critical("RateSheet email did not send first attempt.")
            response = -1
            max_attempts = 10
            count = 0

            # Attempt to send email again, with max retries of 10.
            while response == -1 and count <= max_attempts:

                sleep(3)

                try:
                    response = Emails.bbe_email(gobox_request=gobox_request, files=files)
                except SMTPDataError as e:
                    continue

                if response != -1:
                    break

                count += 1

            if count == max_attempts:
                LOGGER.critical('BBE email exceeded max attempts: {}'.format(gobox_request))

    @app.task(bind=True)
    def mlcarrier_email(self, gobox_request: dict, files: list, ship_data: dict):
        """
            Send shipment request to freight forwarding
            :param files:
            :param gobox_request: shipment request
            :return: None
        """

        # Attempt to send request email
        try:
            response = Emails.mlcarrier_email(gobox_request=gobox_request, files=files, ship_data=ship_data)
        except SMTPDataError as e:
            LOGGER.critical("ML Carrier email did not send first attempt.")
            response = -1
            max_attempts = 10
            count = 0

            # Attempt to send email again, with max retries of 10.
            while response == -1 and count <= max_attempts:

                sleep(3)

                try:
                    response = Emails.bbe_email(gobox_request=gobox_request, files=files)
                except SMTPDataError as e:
                    continue

                if response != -1:
                    break

                count += 1

            if count == max_attempts:
                LOGGER.critical('ML Carrier email exceeded max attempts: {}'.format(gobox_request))

    @app.task(bind=True)
    def skyline_p_d_email(self, data: dict):

        try:
            response = Emails.skyline_pd_email(context=data)
        except SMTPDataError as e:
            LOGGER.critical("RateSheet email did not send first attempt.")
            response = -1
            max_attempts = 10
            count = 0

            # Attempt to send email again, with max retries of 10.
            while response == -1 and count <= max_attempts:

                sleep(3)

                try:
                    response = Emails.skyline_pd_email(context=data)
                except SMTPDataError as e:
                    continue

                if response != -1:
                    break

                count += 1

            if count == max_attempts:
                LOGGER.critical('Skyline P&D email exceeded max attempts: {}'.format(data))

    @app.task(bind=True)
    def interline_email(self, data: dict, email: str):

        try:
            response = Emails.interline_email(context=data, email=email)
        except SMTPDataError as e:
            LOGGER.critical("Interline email did not send first attempt.")
            response = -1
            max_attempts = 10
            count = 0

            # Attempt to send email again, with max retries of 10.
            while response == -1 and count <= max_attempts:

                sleep(3)

                try:
                    response = Emails.interline_email(context=data, email=email)
                except SMTPDataError as e:
                    continue

                if response != -1:
                    break

                count += 1

            if count == max_attempts:
                LOGGER.critical('Interline email exceeded max attempts: {}'.format(data))

    @app.task(bind=True)
    def pickup_issue_email(self, data: dict, carrier: str, order_number: str, pickup_data: dict, is_fail: bool):

        try:
            response = Emails.pickup_issue_email(
                data=data, carrier=carrier,
                order_number=order_number,
                pickup_data=pickup_data,
                is_fail=is_fail
            )
        except SMTPDataError as e:
            LOGGER.critical("RateSheet email did not send first attempt.")
            response = -1
            max_attempts = 10
            count = 0

            # Attempt to send email again, with max retries of 10.
            while response == -1 and count <= max_attempts:

                sleep(3)

                try:
                    response = Emails.pickup_issue_email(
                        data=data, carrier=carrier,
                        order_number=order_number,
                        pickup_data=pickup_data,
                        is_fail=is_fail
                    )
                except SMTPDataError as e:
                    continue

                if response != -1:
                    break

                count += 1

            if count == max_attempts:
                LOGGER.critical('Skyline P&D email exceeded max attempts: {}'.format(data))

    @app.task(bind=True)
    def confirmation_email(self, data: dict, email: str):
        """
            Send shipment request to rate sheet carrier
            :param email:
            :param context: shipment request
            :return: None
        """

        # Attempt to send request email
        try:
            response = Emails.confirmation_email(data=data, email=email)
        except SMTPDataError as e:
            LOGGER.critical("Confirmation email did not send first attempt. {}".format(e))
            response = -1
            max_attempts = 10
            count = 0

            # Attempt to send email again, with max retries of 10.
            while response == -1 and count <= max_attempts:

                sleep(3)

                try:
                    response = Emails.confirmation_email(data=data, email=email)
                except SMTPDataError as e:
                    continue

                if response != -1:
                    break

                count += 1

            if count == max_attempts:
                LOGGER.critical('Confirmation email exceeded max attempts: {}'.format(data))

        if data.get("insurance_amount", "0.00") != "0.00":
            response = Emails.insurance_email(data=data)

    @app.task(bind=True)
    def insurance_email(self, data: dict):
        """
            Send shipment request to rate sheet carrier
            :param data: shipment request
            :return: None
        """

        # Attempt to send request email
        try:
            response = Emails.insurance_email(data=data)
        except SMTPDataError as e:
            LOGGER.critical("Insurance email did not send first attempt. {}".format(e))
            response = -1
            max_attempts = 10
            count = 0

            # Attempt to send email again, with max retries of 10.
            while response == -1 and count <= max_attempts:

                sleep(3)

                try:
                    response = Emails.insurance_email(data=data)
                except SMTPDataError as e:
                    continue

                if response != -1:
                    break

                count += 1

            if count == max_attempts:
                LOGGER.critical('Insurance email exceeded max attempts: {}'.format(data))

    @app.task(bind=True)
    def cancel_shipment_email(self, request: dict):
        """
            Send Cancel shipment request to Customer Service
            :param request: Cancel shipment request
            :return: None
        """
        # Attempt to send request email
        try:
            response = Emails.cancel_shipment_email(context=request)
        except SMTPDataError as e:
            LOGGER.critical("Cancel Shipment email did not send first attempt. {}".format(e))
            response = -1
            max_attempts = 10
            count = 0

            # Attempt to send email again, with max retries of 10.
            while response == -1 and count <= max_attempts:

                sleep(3)

                try:
                    response = Emails.cancel_shipment_email(context=request)
                except SMTPDataError as e:
                    continue

                if response != -1:
                    break

                count += 1

            if count == max_attempts:
                LOGGER.critical('Cancel Shipment email exceeded max attempts: {}'.format(request))

    @app.task(bind=True)
    def cancel_pickup_email(self, request: dict):
        """
            Send Cancel shipment request to Customer Service
            :param request: Cancel shipment request
            :return: None
        """
        # Attempt to send request email
        try:
            response = Emails.cancel_pickup_email(context=request)
        except SMTPDataError as e:
            LOGGER.critical("Cancel Shipment email did not send first attempt. {}".format(e))
            response = -1
            max_attempts = 10
            count = 0

            # Attempt to send email again, with max retries of 10.
            while response == -1 and count <= max_attempts:

                sleep(3)

                try:
                    response = Emails.cancel_pickup_email(context=request)
                except SMTPDataError as e:
                    continue

                if response != -1:
                    break

                count += 1

            if count == max_attempts:
                LOGGER.critical('Cancel Shipment email exceeded max attempts: {}'.format(request))

    @app.task(bind=True)
    def receipt_email(self, data: dict, file: str):
        """
            Send shipment request to customer
            :param file:
            :param data: shipment request
            :return: None
        """

        # Attempt to send request email
        try:
            response = Emails.receipt_email(data=data, files=[file])
        except SMTPDataError as e:
            LOGGER.critical("Receipt email did not send first attempt. {}".format(e))
            response = -1
            max_attempts = 10
            count = 0

            # Attempt to send email again, with max retries of 10.
            while response == -1 and count <= max_attempts:

                sleep(3)

                try:
                    response = Emails.receipt_email(data=data, files=[file])
                except SMTPDataError as e:
                    continue

                if response != -1:
                    break

                count += 1

            if count == max_attempts:
                LOGGER.critical('Receipt email exceeded max attempts: {}'.format(data))
