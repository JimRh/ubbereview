"""
    Title: Business Central SOAP Api
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

from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import ViewException
from brain import settings
from brain.settings import BC_CUSTOMERS_URL, BC_USER, BC_PASS


class BusinessCentralCustomers:
    _ubbe_history = None
    _ubbe_client = None
    _url = BC_CUSTOMERS_URL

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
           Create business central connection for customers.
       """

        if settings.DEBUG:
            wsdl = 'api/apis/business_central/customers/wsdl/dev_customers.wsdl'
        else:
            wsdl = 'api/apis/business_central/customers/wsdl/prod_customers.wsdl'

        self._ubbe_history = HistoryPlugin()
        self._ubbe_client = CachingClient(
            wsdl,
            transport=self._default_transport(),
            plugins=[self._ubbe_history]
        )

    def _post(self) -> list:
        """
            Create get request for all Business Central customers.
            :return: Response Data for Read Multiple
        """

        try:
            ubbe_service = self._ubbe_client.create_service(
                '{urn:microsoft-dynamics-schemas/page/customers_ubbe}Customers_Ubbe_Binding',
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
            CeleryLogger.l_critical.delay(location="KC TESTING", message=f"Data: {sent}Fault: {data}")
            errors = [{"customers": f"Data: {sent}Fault: {data}"}]
            raise ViewException(code="7400", message="BC Customer: Fault in post to customers endpoint.", errors=errors)

        return response

    @staticmethod
    def _format_response(response: list) -> list:
        """
            Format business central customers response into a ubbe naming conventions for ubbe api response
            :param response:
            :return:
        """
        data = []

        for customer in response:

            data.append({
                "no": customer["No"],
                "name": customer["Name"]
            })

        return data

    def read_multiple(self) -> list:
        """
            Get Multiple Customers from Business Central.
            :return: list of customers.
        """

        data = self._post()

        return self._format_response(response=data)
