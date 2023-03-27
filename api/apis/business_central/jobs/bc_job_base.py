"""
    Title: Business Central Jobs SOAP api
    Description: This file will contain all functions to get  Business Central Jobs.
    Created: April 12, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""

import simplejson as json
import copy

from lxml import etree
from requests import Session
from requests_ntlm import HttpNtlmAuth
from zeep import CachingClient, Transport
from zeep.cache import InMemoryCache
from zeep.exceptions import Fault
from zeep.helpers import serialize_object
from zeep.plugins import HistoryPlugin

from api.apis.business_central.exceptions import BusinessCentralError
from api.background_tasks.logger import CeleryLogger
from brain import settings
from brain.settings import BC_JOBS_URL, BC_USER, BC_PASS


class BCJobBase:
    _ubbe_history = None
    _ubbe_client = None
    _url = BC_JOBS_URL

    # Default Values
    _directive_category = 1
    _one = 1
    _zero = 0
    _hundred = 100
    _g_l_account = 3

    # ubbe values
    _air = "AI"
    _courier = "CO"
    _ltl = "LT"
    _ftl = "FT"
    _sealift = "SE"

    # NAV Modes
    _nav_air = 1
    _nav_water = 2
    _nav_ground_truck = 3
    _nav_ground_rail = 4

    def __init__(self, ubbe_data: dict, shipment):
        self._ubbe_data = copy.deepcopy(ubbe_data)
        self._shipment = copy.deepcopy(shipment)

        self._job_number = self._ubbe_data.get("bc_job_number", "")
        self._bc_username = self._ubbe_data.get("bc_username", "")
        self._bc_location = self._ubbe_data.get("bc_location", "")

    @staticmethod
    def _default_transport():
        """
            Transport Layer for authentication.
            :return:
        """
        session = Session()
        session.auth = HttpNtlmAuth(BC_USER, BC_PASS)
        return Transport(cache=InMemoryCache(), session=session)

    @property
    def ubbe_history(self):
        """
            ubbe history
        :return:
        """
        return self._ubbe_history

    @property
    def ubbe_client(self):
        """
            ubbe client
            :return:
        """
        return self._ubbe_client

    def set_bc_connection(self, connection):
        """
            Set business central connection for jobs.
            :return:
        """
        self._ubbe_history = connection.ubbe_history
        self._ubbe_client = connection.ubbe_client

    def create_bc_connection(self):
        """
             Create business central connection for jobs.
            :return:
        """

        if settings.DEBUG:
            # wsdl = 'api/apis/business_central/jobs/wsdl/dev_jobs.wsdl'
            wsdl = 'api/apis/business_central/jobs/wsdl/beta_jobs.wsdl'
        else:
            wsdl = 'api/apis/business_central/jobs/wsdl/prod_jobs.wsdl'

        self._ubbe_history = HistoryPlugin()
        self._ubbe_client = CachingClient(
            wsdl,
            transport=self._default_transport(),
            plugins=[self._ubbe_history]
        )

    def _post(self, request: dict):
        """
            Post ubbe shipment information to Business Central.
            :return: Response Data for ubbe Request
        """

        try:
            ubbe_service = self._ubbe_client.create_service(
                '{urn:microsoft-dynamics-schemas/codeunit/Jobs_Ubbe}Jobs_Ubbe_Binding',
                self._url
            )

            data = {
                "jSONData": json.dumps(request)
            }

            response = serialize_object(ubbe_service.UbbeRequest(**data))

        except Fault:
            data = etree.tounicode(self._ubbe_history.last_received['envelope'])

            CeleryLogger().l_critical.delay(
                location="bc_job_base.py line: 120",
                message=f"{etree.tounicode(self._ubbe_history.last_sent['envelope'], pretty_print=True)} - {data}"
            )
            raise BusinessCentralError(message="BC Fault", data=data)

        if not response:
            return ""

        response = json.loads(response)

        if 'ErrorCode' in response:
            if response["ErrorCode"] != "":
                CeleryLogger().l_critical.delay(
                    location="bc_base.py line: 68",
                    message=str(response)
                )
                raise BusinessCentralError(
                    message="Error: {}. \nMessage: {}.".format(response["ErrorCode"], response["ErrorCode"]),
                    data=response
                )
            else:
                return response["ErrorCode"]

        if 'ResultCode' in response:
            return response["ResultCode"]

        return response
