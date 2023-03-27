from zeep import CachingClient, Transport
from zeep.cache import InMemoryCache
from zeep.plugins import HistoryPlugin
from brain.settings import FEDEX_BASE_URL


def _default_transport():
    return Transport(cache=InMemoryCache())


RATE_HISTORY = HistoryPlugin()
RATE_CLIENT = CachingClient(
    "api/apis/carriers/fedex/globals/wsdl/RateService_v24.wsdl",
    transport=_default_transport(),
    plugins=[RATE_HISTORY],
)

RATE_SERVICE = RATE_CLIENT.create_service(
    "{http://fedex.com/ws/rate/v24}RateServiceSoapBinding",
    "{}/rate/v24".format(FEDEX_BASE_URL),
)

SHIP_HISTORY = HistoryPlugin()
SHIP_CLIENT = CachingClient(
    "api/apis/carriers/fedex/globals/wsdl/ShipService_v23.wsdl",
    transport=_default_transport(),
    plugins=[SHIP_HISTORY],
)

SHIP_SERVICE = SHIP_CLIENT.create_service(
    "{http://fedex.com/ws/ship/v23}ShipServiceSoapBinding",
    "{}/ship/v23".format(FEDEX_BASE_URL),
)

PICKUP_HISTORY = HistoryPlugin()
PICKUP_CLIENT = CachingClient(
    "api/apis/carriers/fedex/globals/wsdl/PickupService_v17.wsdl",
    transport=_default_transport(),
    plugins=[PICKUP_HISTORY],
)
PICKUP_SERVICE = PICKUP_CLIENT.create_service(
    "{http://fedex.com/ws/pickup/v17}PickupServiceSoapBinding",
    "{}/pickup/v17".format(FEDEX_BASE_URL),
)

SERVICE_HISTORY = HistoryPlugin()
SERVICE_CLIENT = CachingClient(
    "api/apis/carriers/fedex/globals/wsdl/ValidationAvailabilityAndCommitmentService_v8.wsdl",
    transport=_default_transport(),
    plugins=[SERVICE_HISTORY],
)
SERVICE_SERVICE = SERVICE_CLIENT.create_service(
    "{http://fedex.com/ws/vacs/v8}ValidationAvailabilityAndCommitmentServiceSoapBinding",
    "{}/vacs/v8".format(FEDEX_BASE_URL),
)

TRACK_HISTORY = HistoryPlugin()
TRACK_CLIENT = CachingClient(
    "api/apis/carriers/fedex/globals/wsdl/TrackService_v16.wsdl",
    transport=_default_transport(),
    plugins=[TRACK_HISTORY],
)
TRACK_SERVICE = TRACK_CLIENT.create_service(
    "{http://fedex.com/ws/track/v16}TrackServiceSoapBinding",
    "{}/track/v16".format(FEDEX_BASE_URL),
)
