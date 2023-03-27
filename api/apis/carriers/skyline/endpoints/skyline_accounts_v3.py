import requests
from django.db import connection, transaction

from api.apis.carriers.skyline.exceptions.exceptions import SkylineAccountError
from api.exceptions.project import RequestError
from api.globals.project import DEFAULT_TIMEOUT_SECONDS, LOGGER
from api.models import SkylineAccount, NatureOfGood, SubAccount
from brain.settings import SKYLINE_BASE_URL


class SkylineAccounts:
    _api_key = ""
    _account_list = SKYLINE_BASE_URL + "/BookingAgent/RetrieveAccountList"
    _rate_priorities_list = SKYLINE_BASE_URL + "/RatePriority/GetRatePriorities"
    _nature_of_goods_list = SKYLINE_BASE_URL + "/RatePriority/GetNaturesOfGood"

    def __init__(self, api_key: str, sub_account: SubAccount):
        self._response = []
        self._api_key = api_key
        self._sub_account = sub_account

    def _get_rate_priorities(self, customer_id: int):
        """
        Get the Rate Priorities tied to account tied to an API key
        :param customer_id: Customer ID of skyline account
        :return: List of Rate Priorities returned from Skyline
        """
        data = {
            "CustomerId": customer_id,
            "API_Key": self._api_key,
            "Url": self._rate_priorities_list,
        }

        try:
            rate_priorities = self._post(data=data)
        except RequestError as e:
            LOGGER.critical("Account: rate priorities request error: {}".format(e))
            raise SkylineAccountError(
                "Account: rate priorities request error: {}".format(e)
            )

        return rate_priorities

    def _get_natures_of_goods(self, customer_id: int, rate_priority: int):
        """
        Get the NOGd for Rate Priority
        :param customer_id: Customer ID of skyline account
        :param rate_priority: Rate Priority
        :return: List of NOGS returned from Skyline
        """

        data = {
            "CustomerId": customer_id,
            "RatePriorityId": rate_priority,
            "API_Key": self._api_key,
            "Url": self._nature_of_goods_list,
        }

        try:
            nogs = self._post(data=data)
        except RequestError as e:
            LOGGER.critical("Account: nogs request error: {}".format(e))
            raise SkylineAccountError("Account: nogs request error: {}".format(e))

        return nogs

    def _get_accounts(self) -> list:
        """
        Get the accounts tied to an API key
        :return: List of accounts returned from Skyline
        """
        data = {"API_Key": self._api_key, "Url": self._account_list}

        try:
            accounts = self._post(data=data)
        except RequestError as e:
            LOGGER.critical("Account: account request error: {}".format(e))
            raise SkylineAccountError("Account: account request error: {}".format(e))

        return accounts

    @transaction.atomic
    def _map_nature_of_goods(self, account: SkylineAccount):
        """
        Map Nature of goods to Rate Priorities and create them.
        :param account: SkylineAccount
        """

        rate_priorities = self._get_rate_priorities(customer_id=account.customer_id)

        for rate_priority in rate_priorities:
            rp = rate_priority.get("RatePriorityId", "")
            rpc = rate_priority.get("RatePriorityCode", "")
            rpd = rate_priority.get("RatePriorityName", "")

            nogs = self._get_natures_of_goods(
                customer_id=account.customer_id, rate_priority=rp
            )

            for customer_nog in nogs:
                nog = NatureOfGood(
                    skyline_account=account,
                    rate_priority_id=rp,
                    rate_priority_code=rpc,
                    rate_priority_description=rpd,
                    nog_id=customer_nog.get("Id", ""),
                    nog_description=customer_nog.get("Description", ""),
                    nog_type="DR",
                ).save()

    @transaction.atomic
    def accounts(self):
        try:
            accounts = self._get_accounts()
        except SkylineAccountError as e:
            raise SkylineAccountError(e.message)

        for account in accounts:
            skyline_account = SkylineAccount(
                sub_account=self._sub_account,
                skyline_account=account.get("AccountNumber"),
                customer_id=account.get("CustomerId"),
            )

            skyline_account.save()

            try:
                self._map_nature_of_goods(account=skyline_account)
            except SkylineAccountError as e:
                raise SkylineAccountError(e.message)

    def _build(self) -> None:
        pass

    def _format_response(self):
        pass

    def _post(self, data: dict):
        """
        Make Skyline calls for account, rate priority, and nature of goods.
        """
        LOGGER.info("Skyline Account posting data: %s", data)

        url = data.pop("Url")

        try:
            response = requests.post(url, json=data, timeout=DEFAULT_TIMEOUT_SECONDS)
        except requests.RequestException:
            connection.close()
            raise RequestError(None, data)

        if not response.ok:
            connection.close()
            raise RequestError(None, data)

        try:
            response = response.json()
        except ValueError:
            connection.close()
            raise RequestError(None, data)

        if response["errors"]:
            connection.close()
            raise RequestError(response, data)

        LOGGER.info("Skyline Account return data: %s", response)

        return response["data"]
