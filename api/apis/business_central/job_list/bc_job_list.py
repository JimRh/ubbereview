"""
    Title: Business Central SOAP Api
    Description: This file will contain all functions to get  Business Central Job List.
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
from zeep.exceptions import Fault, TransportError
from zeep.helpers import serialize_object
from zeep.plugins import HistoryPlugin

from api.apis.business_central.exceptions import BusinessCentralError
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import ViewException
from brain import settings
from brain.settings import BC_JOB_LIST_URL, BC_USER, BC_PASS


class BusinessCentralJobList:
    _ubbe_history = None
    _ubbe_client = None
    _url = BC_JOB_LIST_URL

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
           Create business central connection for job list.
       """

        if settings.DEBUG:
            wsdl = 'api/apis/business_central/job_list/wsdl/beta_job_list.wsdl'
        else:
            wsdl = 'api/apis/business_central/job_list/wsdl/prod_job_list.wsdl'

        self._ubbe_history = HistoryPlugin()
        self._ubbe_client = CachingClient(
            wsdl,
            transport=self._default_transport(),
            plugins=[self._ubbe_history]
        )

    def _post(self, username: str, is_all: bool) -> list:
        """
            Create get request for all Business Central Job list.
            :return: Response Data for Read Multiple
        """

        try:
            ubbe_service = self._ubbe_client.create_service(
                '{urn:microsoft-dynamics-schemas/page/ubbe_job_list}Ubbe_Job_List_Binding',
                self._url
            )

            data = {
                "filter": {
                    "Field": "" if is_all else "File_Owner",
                    "Criteria": "" if is_all else username
                },
                "setSize": 9999
            }

            response = serialize_object(ubbe_service.ReadMultiple(**data))
        except Fault:
            data = etree.tounicode(self._ubbe_history.last_received['envelope'])
            sent = etree.tounicode(self._ubbe_history.last_sent['envelope'], pretty_print=True)
            CeleryLogger.l_critical.delay(location="KC TESTING", message=f"Data: {sent}Fault: {data}")
            errors = [{"job_list": f"Data: {sent}Fault: {data}"}]
            raise ViewException(code="7700", message="BC Job List: Fault in post to job list endpoint.", errors=errors)
        except TransportError as e:
            CeleryLogger.l_critical.delay(location="KC TESTING", message=f"Data: {str(e)}")
            errors = [{"job_list": f"Data:"}]
            raise ViewException(code="7700", message="BC Job List: Fault in post to job list endpoint.", errors=errors)

        return response

    @staticmethod
    def _format_response(response: list) -> list:
        """
            Format business central job list response into a ubbe naming conventions for ubbe api response
            :param response:
            :return:
        """
        data = []

        for job in response:

            data.append({
                "no": job["No"],
                "description": job["Description"],
                "bill_to_customer_no": job["Bill_to_Customer_No"],
                "bill_to_name": job["Bill_to_Name"],
                "created_by": job["Created_By"],
                "file_owner": job["File_Owner"]
            })

        return data

    def read_multiple(self, username: str, is_all: bool) -> list:
        """
            Get Multiple Job List from Business Central.
            :return: list of customers.
        """

        data = self._post(username=username, is_all=is_all)

        if not data:
            return []

        return self._format_response(response=data)
