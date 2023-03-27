import copy
import datetime
from decimal import Decimal

import pytz

from api.apis.carriers.fedex.globals.globals import (
    DROPOFF_TYPE,
    PACKAGING_TYPE,
    MONETARY_CURRENCY,
    RATE_REQUEST_TYPE,
    ESTIMATE_DUTIES_TAXES,
    SERVICES_CA_DICT,
    SERVICES_INT_DICT,
)
from api.apis.carriers.fedex.soap_objects.common.contact_and_address import (
    ContactAndAddress,
)
from api.apis.carriers.fedex.soap_objects.common.party import Party
from api.apis.carriers.fedex.soap_objects.common.payment import Payment
from api.apis.carriers.fedex.soap_objects.common.shipping_document_specification import (
    ShippingDocumentSpecification,
)
from api.apis.carriers.fedex.soap_objects.common.tracking_id import TrackingId
from api.apis.carriers.fedex.soap_objects.ship.customs_clearance_detail import (
    CustomsClearanceDetail,
)
from api.apis.carriers.fedex.soap_objects.ship.label_specification import (
    LabelSpecification,
)
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject
from api.apis.carriers.fedex.utility.utility import FedexUtility


class RequestedShipment(FedExSoapObject):
    _required_keys = {
        "ShipTimestamp",
        "DropoffType",
        "ServiceType",
        "PackagingType",
        "Shipper",
        "Recipient",
        "LabelSpecification",
        "PackageCount",
    }
    _optional_keys = {
        "TotalWeight",
        "TotalInsuredValue",
        "PreferredCurrency",
        "ShipmentAuthorizationDetail",
        "RecipientLocationNumber",
        "Origin",
        "SoldTo",
        "ShippingChargesPayment",
        "SpecialServicesRequested",
        "ExpressFreightDetail",
        "FreightShipmentDetail",
        "DeliveryInstructions",
        "VariableHandlingChargeDetail",
        "CustomsClearanceDetail",
        "PickupDetail",
        "SmartPostDetail",
        "BlockInsightVisibility",
        "ShippingDocumentSpecification",
        "RateRequestTypes",
        "EdtRequestType",
        "MasterTrackingId",
        "ConfigurationData",
        "RequestedPackageLineItems",
    }

    def __init__(
        self,
        gobox_request: dict,
        master_tracking=None,
        sequence=None,
        num_packages: int = None,
    ):
        delivery_instructions = []
        origin = gobox_request["origin"]
        destination = gobox_request["destination"]
        is_international = gobox_request.get("is_international", False)

        if is_international:
            service_type = SERVICES_INT_DICT[gobox_request["service_code"]]
        else:
            service_type = SERVICES_CA_DICT[gobox_request["service_code"]]

        if gobox_request.get("awb"):
            delivery_instructions.append("AWB: {}.".format(gobox_request["awb"]))

        if gobox_request.get("special_instructions"):
            delivery_instructions.append(gobox_request["special_instructions"])

        total_weight, _, packages = FedexUtility.process_packages(
            gobox_request=gobox_request, sequence=sequence
        )

        if "unmodified_packages" in gobox_request:
            gobox_packages = gobox_request["unmodified_packages"]
            total_weight_val = Decimal(0)
            for package in gobox_packages:
                total_weight_val += Decimal(package["quantity"]) * Decimal(
                    package["weight"]
                )
            total_weight = {"Units": "KG", "Value": total_weight_val}

        super().__init__(
            {
                "DropoffType": DROPOFF_TYPE,
                "PackagingType": PACKAGING_TYPE,
                "PreferredCurrency": MONETARY_CURRENCY,
                "Shipper": Party(party_details=origin).data,
                "Recipient": Party(party_details=destination).data,
                "Origin": ContactAndAddress(party_details=origin).data,
                "ShippingChargesPayment": Payment(
                    account_number=gobox_request["account_number"]
                ).data,
                "LabelSpecification": LabelSpecification().data,
                "RateRequestTypes": RATE_REQUEST_TYPE,
                "ShipTimestamp": datetime.datetime.now(
                    pytz.timezone("America/Edmonton")
                ),
                "ServiceType": service_type,
                "TotalWeight": total_weight,
                "PackageCount": num_packages,
                "RequestedPackageLineItems": packages,
                "DeliveryInstructions": " ".join(delivery_instructions),
            },
            required_keys=self._required_keys,
            optional_keys=self._optional_keys,
        )

        if master_tracking:
            self.add_value(
                "MasterTrackingId", TrackingId(tracking_number=master_tracking).data
            )

        if is_international:
            customs = []
            for package in gobox_request["packages"]:
                customs.append(
                    CustomsClearanceDetail(
                        recipient=destination,
                        commodities=package["commodities"],
                        broker=gobox_request["broker"],
                        origin=origin,
                    ).data
                )

            self.add_values(
                CustomsClearanceDetail=customs,
                ShippingDocumentSpecification=ShippingDocumentSpecification(
                    is_international=True
                ).data,
                EdtRequestType=ESTIMATE_DUTIES_TAXES,
            )

        # if shipment_request.get('Pickup'):
        #     self.add_value('PickupDetail', PickupDetail(shipment_request['Pickup']))
