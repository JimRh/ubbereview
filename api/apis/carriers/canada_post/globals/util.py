import requests
from zeep import CachingClient, wsse, Transport
from zeep.cache import InMemoryCache
from zeep.plugins import HistoryPlugin

from api.apis.carriers.canada_post.globals.globals import (
    SHIPMENT_WSDL,
    RATE_WSDL,
    MANIFEST_WSDL,
    ARTIFACT_WSDL,
    PICKUP_WSDL,
    PICKUP_REQUEST_WSDL,
)
from api.globals.project import LOGGER, DEFAULT_TIMEOUT_SECONDS
from api.models import CarrierAccount
from brain.settings import (
    CANADA_POST_PICKUP_REQUEST_BASE_URL,
    CANADA_POST_PICKUP_BASE_URL,
    CANADA_POST_BASE_URL,
)


class Endpoints:
    def __init__(self, carrier_account: CarrierAccount):
        self.history_plugin = HistoryPlugin()
        username = carrier_account.username.decrypt()
        password = carrier_account.password.decrypt()

        self.SHIPMENT_CLIENT = CachingClient(
            SHIPMENT_WSDL,
            wsse=wsse.UsernameToken(username, password),
            transport=Transport(cache=InMemoryCache(), timeout=DEFAULT_TIMEOUT_SECONDS),
        )

        self.SHIPMENT_SERVICE = self.SHIPMENT_CLIENT.create_service(
            "{http://www.canadapost.ca/ws/soap/shipment/v8}Shipment",
            CANADA_POST_BASE_URL + "/shipment/v8",
        )

        try:
            self.RATE_CLIENT = CachingClient(
                RATE_WSDL,
                wsse=wsse.UsernameToken(username, password),
                transport=Transport(
                    cache=InMemoryCache(), timeout=DEFAULT_TIMEOUT_SECONDS
                ),
            )

            self.MANIFEST_CLIENT = CachingClient(
                MANIFEST_WSDL,
                wsse=wsse.UsernameToken(username, password),
                transport=Transport(
                    cache=InMemoryCache(), timeout=DEFAULT_TIMEOUT_SECONDS
                ),
            )

            self.ARTIFACT_CLIENT = CachingClient(
                ARTIFACT_WSDL,
                wsse=wsse.UsernameToken(username, password),
                transport=Transport(
                    cache=InMemoryCache(), timeout=DEFAULT_TIMEOUT_SECONDS
                ),
            )

            self.PICKUP_CLIENT = CachingClient(
                PICKUP_WSDL,
                wsse=wsse.UsernameToken(username, password),
                transport=Transport(
                    cache=InMemoryCache(), timeout=DEFAULT_TIMEOUT_SECONDS
                ),
                plugins=[self.history_plugin],
            )

            self.REQUEST_PICKUP_CLIENT = CachingClient(
                PICKUP_REQUEST_WSDL,
                wsse=wsse.UsernameToken(username, password),
                transport=Transport(
                    cache=InMemoryCache(), timeout=DEFAULT_TIMEOUT_SECONDS
                ),
                plugins=[self.history_plugin],
            )

        except requests.exceptions.RequestException as e:
            LOGGER.critical(
                "Canada Post SOAP clients could not be instantiated.\n%s", e
            )
        else:
            self.RATE_SERVICE = self.RATE_CLIENT.create_service(
                "{http://www.canadapost.ca/ws/soap/ship/rate/v4}Rating",
                CANADA_POST_BASE_URL + "/rating/v4",
            )

            self.MANIFEST_SERVICE = self.MANIFEST_CLIENT.create_service(
                "{http://www.canadapost.ca/ws/soap/manifest/v8}Manifest",
                CANADA_POST_BASE_URL + "/manifest/v8",
            )

            self.ARTIFACT_SERVICE = self.ARTIFACT_CLIENT.create_service(
                "{http://www.canadapost.ca/ws/soap/artifact}Artifact",
                CANADA_POST_BASE_URL + "/artifact",
            )

            self.PICKUP_SERVICE = self.PICKUP_CLIENT.create_service(
                "{http://www.canadapost.ca/ws/soap/pickup/availability}PickupDomain",
                CANADA_POST_PICKUP_BASE_URL + "/pickup/availability",
            )

            self.REQUEST_PICKUP_SERVICE = self.REQUEST_PICKUP_CLIENT.create_service(
                "{http://www.canadapost.ca/ws/soap/pickuprequest}PickupRequest",
                CANADA_POST_PICKUP_REQUEST_BASE_URL + "/pickuprequest",
            )
