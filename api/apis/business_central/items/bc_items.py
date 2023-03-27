"""
    Title: Business Central Items SOAP api
    Description: This file will contain all functions to get  Business Central Customers.
    Created: April 12, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from lxml import etree
from requests import Session
from requests_ntlm import HttpNtlmAuth
from zeep import CachingClient, Transport
from zeep.cache import InMemoryCache
from zeep.exceptions import Fault
from zeep.helpers import serialize_object
from zeep.plugins import HistoryPlugin

from api.exceptions.project import ViewException
from brain import settings
from brain.settings import BC_ITEMS_URL, BC_USER, BC_PASS


class BusinessCentralItems:
    _ubbe_history = None
    _ubbe_client = None
    _url = BC_ITEMS_URL

    def __init__(self):
        self.create_bc_connection()

    @staticmethod
    def _default_transport():
        """
            Transport Layer for authentication.
            :return:
        """
        session = Session()
        session.auth = HttpNtlmAuth(BC_USER, BC_PASS)
        return Transport(cache=InMemoryCache(), session=session)

    def create_bc_connection(self) -> None:
        """
           Create business central connection for items.
       """

        if settings.DEBUG:
            # wsdl = 'api/apis/business_central/items/wsdl/dev_items.wsdl'
            wsdl = 'api/apis/business_central/items/wsdl/beta_items.wsdl'
        else:
            wsdl = 'api/apis/business_central/items/wsdl/prod_items.wsdl'

        self._ubbe_history = HistoryPlugin()
        self._ubbe_client = CachingClient(
            wsdl,
            transport=self._default_transport(),
            plugins=[self._ubbe_history]
        )

    def _post(self) -> list:
        """
            Create get request for all Business Central items.
            :return: Response Data for Read Multiple
        """

        try:
            ubbe_service = self._ubbe_client.create_service(
                '{urn:microsoft-dynamics-schemas/page/items_ubbe}Items_Ubbe_Binding',
                self._url
            )

            data = {
                "filter": {
                    "Field": "",
                    "Criteria": ""
                },
                "setSize": 9999
            }

            response = serialize_object(ubbe_service.ReadMultiple(**data))

        except Fault:
            data = etree.tounicode(self._ubbe_history.last_received['envelope'])
            sent = etree.tounicode(self._ubbe_history.last_sent['envelope'], pretty_print=True)
            errors = [{"items": f"Data: {sent}Fault: {data}"}]
            raise ViewException(code="7500", message="BC Item: Fault in post to items endpoint.", errors=errors)

        return response

    @staticmethod
    def _format_response(response: list) -> list:
        """
            Format business central items response into a ubbe naming conventions for ubbe api response
            :param response:
            :return:
        """
        data = []

        for customer in response:

            data.append({
                "no": customer["No"],
                "description": customer["Description"]
            })

        return data

    def read_multiple(self):
        """
            Get Multiple Items from Business Central.
            :return: list of items.
        """

        data = self._post()

        return self._format_response(response=data)
