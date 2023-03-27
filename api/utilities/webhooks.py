"""
    Title: Webhook Event handler
    Description:
        The class will handle posting webhook events to the client and create necessary verification headers such as,
        hmac signature, account number, and topic. The last part is to post the details to the registared url.
    Created: July 13, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

import copy
import hashlib
import hmac

import requests
import simplejson as json
from typing import Union

from django.db import connection

from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import RequestError
from api.globals.project import WEBHOOK_TIMEOUT_SECONDS
from api.models import SubAccount, Webhook


class WebHookEvent:

    def __init__(self, data: Union[list, dict], sub_account: SubAccount, webhook: Webhook) -> None:
        self._data = copy.deepcopy(data)
        self._webhook = webhook
        self._sub_account = sub_account

    def create_hmac(self) -> str:
        """
            Create hmac for webhook event for Keyed-Hashing Message Authentication.
            :return: hmac
        """

        data_str = json.dumps(self._data)

        signature = hmac.new(
            str(self._sub_account.webhook_key).encode('utf-8'),
            msg=data_str.encode('utf-8'),
            digestmod=hashlib.sha3_512
        ).hexdigest()

        return signature

    def get_headers(self, signature: str):
        """
            Get headers for webhook event post.
            :param signature: hmac
            :return:
        """

        return {
            "X-UBBE-TOPIC": self._webhook.get_event_display().replace(" ", ""),
            "X-UBBE-ACCOUNT": str(self._sub_account.subaccount_number),
            "X-UBBE-HMAC": signature,
        }

    def send_event(self) -> None:
        """
            Perform webhook event post for a given event.
            :return:
        """
        signature = self.create_hmac()
        headers = self.get_headers(signature=signature)

        try:
            response = requests.post(
                url=self._webhook.url, json=self._data, headers=headers, timeout=WEBHOOK_TIMEOUT_SECONDS
            )
        except requests.Timeout:
            connection.close()
            # Request took to long to response: 10 seconds.
            return None
        except requests.RequestException:
            connection.close()

            CeleryLogger().l_info.delay(
                location="webhook.py line: 79",
                message=f"Webhook data: {self._webhook.event} - {self._data}"
            )

            raise RequestError(None, self._data)

        if response.ok:
            # Webhooks should return status 200 for success.
            return None

        return None
