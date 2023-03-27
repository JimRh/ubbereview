"""
    Title: Purolator Freight Api
    Description: This file will contain functions related to Purolator Freight base Apis.
    Created: December 14, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""

import copy

import zeep
from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import CachingClient, Transport
from zeep.cache import InMemoryCache
from zeep.plugins import HistoryPlugin

from api.globals.carriers import PUROLATOR_FREIGHT
from brain import settings


class PurolatorFreightApi:
    """
    Purolator Freight Api Class
    """

    _freight_name = "Purolator Freight"
    _language = "en"
    _history = None
    _client = None
    _name_space = None

    _puro_service = {
        "PurolatorExpress": "Purolator Express®",
    }

    def __init__(self, ubbe_request: dict, is_track: bool = False):
        self._ubbe_request = copy.deepcopy(ubbe_request)

        if not is_track:
            self.sub_account = self._ubbe_request["objects"]["sub_account"]
            self.carrier_account = self._ubbe_request["objects"]["carrier_accounts"][
                PUROLATOR_FREIGHT
            ]["account"]
            self.carrier = self._ubbe_request["objects"]["carrier_accounts"][
                PUROLATOR_FREIGHT
            ]["carrier"]

            self._account_number = self.carrier_account.account_number.decrypt()
            self._password = self.carrier_account.password.decrypt()
            self._key = self.carrier_account.api_key.decrypt()

    @staticmethod
    def _default_transport(user: str, password: str):
        """
        Create default transport and authenticate with user and password.
        :return:
        """
        session = Session()
        session.auth = HTTPBasicAuth(user, password)
        return Transport(cache=InMemoryCache(), session=session)

    def _build_request_context(self, reference: str, version: str):
        """
        Create Request Context header for Purolator Soap call.
        :param reference: Service being called
        :return: RequestContext Object
        """

        header = zeep.xsd.Element(
            "{http://purolator.com/pws/datatypes/v1}RequestContext",
            zeep.xsd.ComplexType(
                [
                    zeep.xsd.Element(
                        "{http://purolator.com/pws/datatypes/v1}Version",
                        zeep.xsd.String(),
                    ),
                    zeep.xsd.Element(
                        "{http://purolator.com/pws/datatypes/v1}Language",
                        zeep.xsd.String(),
                    ),
                    zeep.xsd.Element(
                        "{http://purolator.com/pws/datatypes/v1}GroupID",
                        zeep.xsd.String(),
                    ),
                    zeep.xsd.Element(
                        "{http://purolator.com/pws/datatypes/v1}RequestReference",
                        zeep.xsd.String(),
                    ),
                    zeep.xsd.Element(
                        "{http://purolator.com/pws/datatypes/v1}UserToken",
                        zeep.xsd.String(),
                    ),
                ]
            ),
        )

        return header(
            Version=version,
            Language=self._language,
            GroupID="XXX",
            RequestReference=reference,
            UserToken=self._key,
        )

    def create_connection(self, wsdl_path: str):
        """
        Create SOAP Connect to puro web services.
        :param wsdl_path: Project path
        :return:
        """

        if settings.DEBUG:
            wsdl = f"api/apis/carriers/purolator/freight/wsdl/development/{wsdl_path}"
        else:
            wsdl = f"api/apis/carriers/purolator/freight/wsdl/production/{wsdl_path}"

        self._history = HistoryPlugin()
        self._client = CachingClient(
            wsdl,
            transport=self._default_transport(user=self._key, password=self._password),
            plugins=[self._history],
        )
