import datetime
from typing import Any

from api import logging_data
from brain.settings import SKYLINE_BASE_URL

SKYLINE_TRACK_URL = SKYLINE_BASE_URL + '/LegacyTrackAndTrace/TrackAndTrace'

LOGGER = logging_data.logger_setup('Logger')

DOCUMENT_TYPE_COMMERCIAL_INVOICE = "2"
DOCUMENT_TYPE_B13A = "5"
DOCUMENT_TYPE_DG = "7"

DOCUMENT_TYPE_SHIPPING_LABEL = "1"
DOCUMENT_TYPE_BILL_OF_LADING = "0"
DOCUMENT_TYPE_NEAS = "7"
DOCUMENT_TYPE_NSSI = "7"

DOCUMENT_TYPE_OTHER_DOCUMENT = "99"

DEFAULT_CHAR_LEN = 100
DEFAULT_TEXT_LEN = 2500
POSTAL_CODE_LEN = 12
DEFAULT_ACCOUNT_LEN = 20
ISO_3166_1_LEN = 3
ISO_4217_LEN = 3
COUNTRY_CODE_LEN = ISO_3166_1_LEN
PROVINCE_CODE_LEN = ISO_3166_1_LEN
CURRENCY_CODE_LEN = ISO_4217_LEN
LETTER_MAPPING_LEN = 1
LEG_IDENTIFIER_LEN = 15
SHIPMENT_IDENTIFIER_LEN = 19
PHONE_MIN = 9
PHONE_MAX = 16
EXTENSION_MAX = 15
DIMENSION_PRECISION = 2
PERCENTAGE_PRECISION = 2
EXCHANGE_RATE_PRECISION = 6
PRICE_PRECISION = 2
WEIGHT_BREAK_PRECISION = 4
WEIGHT_PRECISION = 2
DG_PRECISION = 6
BASE_TEN = 10
DEFAULT_KEY_LENGTH = 64
MAX_PACK_ID_LEN = 19
MAX_DIMENSION_DIGITS = 8
MAX_PERCENTAGE_DIGITS = 5
MAX_PRICE_DIGITS = 15
MAX_WEIGHT_BREAK_DIGITS = 17
MAX_WEIGHT_DIGITS = 11
MAX_CHAR_LEN = 255
MAX_INSURANCE_DIGITS = 13
NO_INSURANCE = 0
MAX_TEXT_LEN = 5000
TRANSACTION_RESPONSE_LEN = 25
TRANSACTION_IDENTIFIER_LEN = 19

# Api fields
API_CHAR_LEN = 30
API_CHAR_MID_LEN = 100
API_MAX_CHAR_LEN = 150
API_COUNTRY_CODE_LEN = 2
API_PROVINCE_CODE_LEN = 2
API_MAX_PROVINCE_CODE_LEN = 3
API_PHONE_MIN = 9
API_PHONE_MAX = 16

API_MAX_PACK_CHAR = 40
API_MAX_TIME_CHAR = 5
API_ZERO = 0

API_PACKAGE_ONE = 1
API_PACKAGE_TYPES = (
    ('BAG', 'BAG'),
    ('BOX', 'BOX'),
    ('DG', 'DG'),
    ('BUNDLES', 'BUNDLES'),
    ('CONTAINER', 'CONTAINER'),
    ('CRATE', 'CRATE'),
    ('DRUM', 'DRUM'),
    ('ENVELOPE', 'ENVELOPE'),
    ('PAIL', 'PAIL'),
    ('REEL', 'REEL'),
    ('ROLL', 'ROLL'),
    ('SKID', 'SKID'),
    ('TOTES', 'TOTES'),
    ('TUBE', 'TUBE'),
    ('VEHICLE', 'VEHICLE'),
    ('PHFRO', 'Pharma Frozen (-18C or below)'),
    ('PHREF', 'Pharma Refrigerated (+2C to +8C)'),
    ('PHCONR', 'Pharma Controlled Room (+15C to 25C)'),
    ('PHEXR', 'Pharma Extended Room (+2C to 25C)'),
)

API_PACKAGE_YES_NO = (
    ('NA', 'N/A'),
    ('YES', 'Yes'),
    ('NO', 'No'),
)

API_PACKAGE_CONTAINER_PACKING = (
    ('NA', 'N/A'),
    ('EMPT', 'Empty'),
    ('HALF', 'Half Packed'),
    ('FULL', 'Full Packed'),
)

API_API_CATEGORY = (
    ("AC", "Account Apis"),
    ("AA", "Admin Apis"),
    ("BC", "Business Central Apis"),
    ("CA", "Carrier Apis"),
    ("DG", "Dangerous Goods Apis"),
    ("GA", "Google Apis"),
    ("ME", "Metric Apis"),
    ("lA", "Location Apis"),
    ("MA", "Main Apis"),
    ("OA", "Option Apis"),
    ("RA", "Report Apis"),
    ("SA", "Shipment Apis"),
    ("SK", "Skyline Apis"),
    ("NA", "N/A")
)

API_SYSTEMS = (
    ('UBAPI', 'ubbe Api'),
    ('UBWEB', 'ubbe Web'),
    ('FETCH', 'Fetchable'),
    ('DELIV', 'DeliverEase')
)

AIRPORT_CODE_LEN = 3
GO_PREFIX = "ub"
ID_LENGTH = 12
LEG_ID_LENGTH = 13
POSTAL_CODE_REGEX = {
    "CA": r"[A-Z]\d[A-Z] ?\d[A-Z]\d",
    "US": r"\d{5}"
}
CANADIAN_AREA_CODES = {
    "204", "226", "236", "249", "250", "289", "306", "343", "365", "403", "416", "418", "431", "437", "438", "450",
    "506", "514", "519", "548", "579", "581", "587", "604", "613", "639", "647", "705", "709", "778", "780", "782",
    "800", "807", "819", "825", "867", "873", "888", "902", "905"
}
DEFAULT_STRING_REGEX = r'[`~!@#$^&*()_=+\[\]{\}|;:,./><?%"\\]'
STRICT_STRING_REGEX = r'[\s+`~!@#$^&*()\-_=\[\]{\}|;:,./><?%"\'\\]'

MAX_PICKUP_DAYS_IN_FUTURE = 1444

DEFAULT_TIMEOUT_SECONDS = 60
WEBHOOK_TIMEOUT_SECONDS = 10

BAD_REQUEST = 400
UNAUTHORIZED = 401
FORBIDDEN = 403
NOT_FOUND = 404
METHOD_NOT_ALLOWED = 405
IM_A_TEAPOT = 418
INTERNAL_SERVER_ERROR = 500
HTTP_OK = 200

DEFAULT_PICKUP_START = '07:00'
DEFAULT_PICKUP_END = '16:30'

# Business Central
NEW_FILE = "NF"
UPDATE_FILE = "UF"


def DEFAULT_PICKUP_DATE() -> str:
    return datetime.datetime.today().strftime('%Y-%m-%d')


def getkey(obj: dict, keys: str, default=None) -> Any:
    for key in keys.split('.'):
        if isinstance(obj, dict):
            obj = obj.get(key, default)
        else:
            return default

    return obj
