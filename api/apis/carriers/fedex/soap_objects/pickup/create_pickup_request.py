from decimal import Decimal

from api.apis.carriers.fedex.soap_objects.common.version_id import VersionId
from api.apis.carriers.fedex.soap_objects.common.web_authentication_detail import (
    WebAuthenticationDetail,
)
from api.apis.carriers.fedex.soap_objects.common.weight import Weight
from api.apis.carriers.fedex.soap_objects.pickup.client_detail import ClientDetail
from api.apis.carriers.fedex.soap_objects.pickup.pickup_origin_detail import (
    PickupOriginDetail,
)
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class CreatePickupRequest(FedExSoapObject):
    _required_keys = {"WebAuthenticationDetail", "ClientDetail", "Version"}
    _optional_keys = {
        "TransactionDetail",
        "AssociatedAccountNumber",
        "TrackingNumber",
        "OriginDetail",
        "PickupServiceCategory",
        "FreightPickupDetail",
        "ExpressFreightDetail",
        "PackageCount",
        "TotalWeight",
        "CarrierCode",
        "OversizePackageCount",
        "Remarks",
        "CommodityDescription",
        "CountryRelationship",
    }

    def __init__(self, gobox_request: dict):
        if (
            gobox_request["origin"]["country"]
            == gobox_request["destination"]["country"]
        ):
            country_relationship = "DOMESTIC"
        else:
            country_relationship = "INTERNATIONAL"

        if "92" == gobox_request["service_code"]:
            carrier_code = "FDXG"
        else:
            carrier_code = "FDXE"

        quantity = 0
        weight = Decimal("0.00")

        for package in gobox_request["packages"]:
            quantity += package["quantity"]
            weight += package["weight"]

        version = VersionId(
            version={
                "ServiceId": "disp",
                "Major": 17,
                "Intermediate": 0,
                "Minor": 0,
            }
        )

        client = ClientDetail(
            account_number=gobox_request["account_number"],
            meter_number=gobox_request["meter_number"],
        )

        auth = WebAuthenticationDetail(
            key=gobox_request["key"],
            password=gobox_request["password"],
        )

        super().__init__(
            {
                "WebAuthenticationDetail": auth.data,
                "ClientDetail": client.data,
                "Version": version.data,
                "OriginDetail": PickupOriginDetail(gobox_request=gobox_request).data,
                # 'PickupServiceCategory': None,
                "PackageCount": quantity,
                "TotalWeight": Weight(weight_value=weight).data,
                "CarrierCode": carrier_code,
                "CountryRelationship": country_relationship,
            },
            required_keys=self._required_keys,
            optional_keys=self._optional_keys,
        )
