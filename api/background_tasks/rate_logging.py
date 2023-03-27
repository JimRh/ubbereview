"""
    Title: Celery Rate Logging
    Description: This file will contain functions for Celery Rate Logging.
    Created: May 5, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist

from api.globals.project import LOGGER
from api.models import RateLog, SubAccount
from brain.celery import app


class CeleryRateLog:
    """
        rate log behind the scenes.
    """

    @app.task(bind=True)
    def log_rate(self, rate_request: dict, rate_response: dict, is_no_rate=False) -> None:
        """
            Rate Log for no rates returning.
            :param is_no_rate:
            :param rate_request: ubbe Rate Api Request.
            :param rate_response: ubbe Rate Api Response.
            :return: None
        """

        if RateLog.objects.filter(rate_data=rate_request).exists():
            return None

        try:
            sub_account = SubAccount.objects.get(subaccount_number=rate_request["account_number"])
        except Exception as e:
            LOGGER.info(f'{str(e)}')
            return None

        try:
            log = RateLog.create(
                param_dict={
                    "sub_account": sub_account,
                    "rate_data": rate_request,
                    "response_data": rate_response,
                    "is_no_rate": is_no_rate
                }
            )
            log.save()
        except Exception as e:
            LOGGER.info(f'{str(e)}')

    @app.task(bind=True)
    def log_rate_response(self, rate_log_id: str, rate_response: dict) -> None:
        """
            Rate Log for no rates returning.
            :param rate_log_id:
            :param rate_response: ubbe Rate Api Response.
            :return: None
        """
        rate_log = RateLog.objects.get(rate_log_id=rate_log_id)
        rate_log.response_data = rate_response
        rate_log.is_no_rate = False
        rate_log.save()

    @app.task(bind=True)
    def log_rate_selected_response(self, rate_log_id: str, ship_request: dict, shipment_id: str) -> None:
        """
            Rate Log for no rates returning.
            :param rate_log_id: Log Id
            :param ship_request: ubbe Ship Api Request.
            :param shipment_id: ubbe Shipment id.
            :return: None
        """

        try:
            rate_log = RateLog.objects.get(rate_log_id=rate_log_id)
        except ObjectDoesNotExist as e:
            return

        rate_log.ship_data = ship_request
        rate_log.shipment_id = shipment_id
        rate_log.save()
