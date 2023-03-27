"""
    Title: Purolator Api
    Description: This file will contain functions related to Purolator base Apis.
    Created: December 7, 2020
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

from api.globals.carriers import PUROLATOR
from brain import settings


class PurolatorBaseApi:
    """
    Purolator Api Class
    """

    _courier_name = "Purolator"

    _language = "en"

    _history = None
    _client = None
    _name_space = None

    _puro_service = {
        "PurolatorExpress": "Purolator Express®",
        "PurolatorExpress9AM": "Purolator Express® 9AM",
        "PurolatorExpress10:30AM": "Purolator Express® 10:30AM",
        "PurolatorExpress12PM": "Purolator Express® 12PM",
        "PurolatorExpressEvening": "Purolator Express® Evening",
        "PurolatorExpressEnvelope": "Purolator Express® Envelope",
        "PurolatorExpressEnvelope9AM": "Purolator Express® Envelope 9AM",
        "PurolatorExpressEnvelope10:30AM": "Purolator Express® Envelope 10:30AM",
        "PurolatorExpressEnvelope12PM": "Purolator Express® Envelope 12PM",
        "PurolatorExpressEnvelopeEvening": "Purolator Express® Envelope Evening",
        "PurolatorExpressPack9AM": "Purolator Express® Pack 9AM",
        "PurolatorExpressPack10:30AM": "Purolator Express® Pack 10:30AM",
        "PurolatorExpressPack12PM": "Purolator Express® Pack 12PM",
        "PurolatorExpressPack": "Purolator Express® Pack",
        "PurolatorExpressPackEvening": "Purolator Express® Pack Evening",
        "PurolatorExpressBox9AM": "Purolator Express® Box 9AM",
        "PurolatorExpressBox10:30AM": "Purolator Express® Box 10:30AM",
        "PurolatorExpressBox12PM": "Purolator Express® Box 12PM",
        "PurolatorExpressBox": "Purolator Express® Box",
        "PurolatorExpressBoxEvening": "Purolator Express® Box Evening",
        "PurolatorGround": "Purolator Ground®",
        "PurolatorGround9AM": "Purolator Ground® 9AM",
        "PurolatorGround10:30AM": "Purolator Ground® 10:30AM",
        "PurolatorGroundEvening": "Purolator Ground® Evening",
        "PurolatorQuickShip": "Purolator QuickShipTM",
        "PurolatorQuickShipEnvelope": "Purolator QuickShipTM Envelope",
        "PurolatorQuickShipPack": "Purolator QuickShipTM Pack",
        "PurolatorQuickShipBox": "Purolator QuickShipTM Box",
        "PurolatorExpressU.S.": "Purolator Express® U.S.",
        "PurolatorExpressU.S.9AM": "Purolator Express® U.S. 9AM",
        "PurolatorExpressU.S.10:30AM": "Purolator Express® U.S. 10:30AM",
        "PurolatorExpressU.S.12:00": "Purolator Express® U.S. 12PM",
        "PurolatorExpressEnvelopeU.S.": "Purolator Express® Envelope U.S.",
        "PurolatorExpressU.S.Envelope9AM": "Purolator Express® Envelope U.S. 9AM",
        "PurolatorExpressU.S.Envelope10:30AM": "Purolator Express® Envelope U.S. 10:30AM",
        "PurolatorExpressU.S.Envelope12:00": "Purolator Express® Envelope U.S. 12PM",
        "PurolatorExpressPackU.S.": "Purolator Express® Pack U.S.",
        "PurolatorExpressU.S.Pack9AM": "Purolator Express® Pack U.S. 9AM",
        "PurolatorExpressU.S.Pack10:30AM": "Purolator Express® Pack U.S. 10:30AM",
        "PurolatorExpressU.S.Pack12:00": "Purolator Express® Pack U.S. 12PM",
        "PurolatorExpressBoxU.S.": "Purolator Express® Box U.S.",
        "PurolatorExpressU.S.Box9AM": "Purolator Express® Box U.S. 9AM",
        "PurolatorExpressU.S.Box10:30AM": "Purolator Express® Box U.S. 10:30AM",
        "PurolatorExpressU.S.Box12:00": "Purolator Express® Box U.S. 12PM",
        "PurolatorGroundU.S.": "Purolator Ground® U.S.",
        "PurolatorExpressInternational": "Purolator Express® International",
        "PurolatorExpressInternational9AM": "Purolator Express® International 9AM",
        "PurolatorExpressInternational10:30AM": "Purolator Express® International 10:30AM",
        "PurolatorExpressInternational12:00": "Purolator Express® International 12PM",
        "PurolatorExpressEnvelopeInternational": "Purolator Express® Envelope International",
        "PurolatorExpressInternationalEnvelope9AM": "Purolator Express® Envelope International 9AM",
        "PurolatorExpressInternationalEnvelope10:30AM": "Purolator Express® Envelope International 10:30AM",
        "PurolatorExpressInternationalEnvelope12:00": "Purolator Express® Envelope International 12PM",
        "PurolatorExpressPackInternational": "Purolator Express® Pack International",
        "PurolatorExpressInternationalPack9AM": "Purolator Express® Pack International 9AM",
        "PurolatorExpressInternationalPack10:30AM": "Purolator Express® Pack International 10:30AM",
        "PurolatorExpressInternationalPack12:00": "Purolator Express® Pack International 12PM",
        "PurolatorExpressBoxInternational": "Purolator Express® Box International",
        "PurolatorExpressInternationalBox9AM": "Purolator Express® Box International 9AM",
        "PurolatorExpressInternationalBox10:30AM": "Purolator Express® Box International 10:30AM",
        "PurolatorExpressInternationalBox12:00": "Purolator Express® Box International 12PM",
    }

    def __init__(self, ubbe_request: dict, is_track: bool = False):
        self._ubbe_request = copy.deepcopy(ubbe_request)

        if not is_track:
            self.sub_account = self._ubbe_request["objects"]["sub_account"]
            self.carrier_account = self._ubbe_request["objects"]["carrier_accounts"][
                PUROLATOR
            ]["account"]
            self.carrier = self._ubbe_request["objects"]["carrier_accounts"][PUROLATOR][
                "carrier"
            ]

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

        version_url = f"http://purolator.com/pws/datatypes/v{version[:1]}"

        header = zeep.xsd.Element(
            "{" + version_url + "}RequestContext",
            zeep.xsd.ComplexType(
                [
                    zeep.xsd.Element("{" + version_url + "}Version", zeep.xsd.String()),
                    zeep.xsd.Element(
                        "{" + version_url + "}Language", zeep.xsd.String()
                    ),
                    zeep.xsd.Element("{" + version_url + "}GroupID", zeep.xsd.String()),
                    zeep.xsd.Element(
                        "{" + version_url + "}RequestReference", zeep.xsd.String()
                    ),
                    zeep.xsd.Element(
                        "{" + version_url + "}UserToken", zeep.xsd.String()
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

    def create_connection(self, wsdl_path: str, version: str):
        """
        Create SOAP Connect to puro web services.
        :param wsdl_path: Project path
        :return:
        """

        if settings.DEBUG:
            wsdl = f"api/apis/carriers/purolator/courier/wsdl/development/{wsdl_path}"
        else:
            wsdl = f"api/apis/carriers/purolator/courier/wsdl/production/{wsdl_path}"

        if version[:1] == "1":
            version_url = "http://purolator.com/pws/datatypes/v1"
        else:
            version_url = "http://purolator.com/pws/datatypes/v2"

        self._history = HistoryPlugin()
        self._client = CachingClient(
            wsdl,
            transport=self._default_transport(user=self._key, password=self._password),
            plugins=[self._history],
        )
        self._client.set_ns_prefix(f"v{version[:1]}", version_url)
