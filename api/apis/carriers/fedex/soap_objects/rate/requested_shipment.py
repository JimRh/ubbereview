from api.apis.carriers.fedex.globals.globals import (
    DROPOFF_TYPE,
    PACKAGING_TYPE,
    MONETARY_CURRENCY,
    RATE_REQUEST_TYPE,
    ESTIMATE_DUTIES_TAXES,
)
from api.apis.carriers.fedex.soap_objects.common.contact_and_address import (
    ContactAndAddress,
)
from api.apis.carriers.fedex.soap_objects.common.party import Party
from api.apis.carriers.fedex.soap_objects.common.payment import Payment
from api.apis.carriers.fedex.soap_objects.common.pickup_detail import PickupDetail
from api.apis.carriers.fedex.soap_objects.rate.label_specification import (
    LabelSpecification,
)
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject
from api.apis.carriers.fedex.utility.utility import FedexUtility


class RequestedShipment(FedExSoapObject):
    _optional_keys = {
        "ShipTimestamp",
        "DropoffType",
        "ServiceType",
        "PackagingType",
        "VariationOptions",
        "TotalWeight",
        "TotalInsuredValue",
        "PreferredCurrency",
        "ShipmentAuthorizationDetail",
        "Shipper",
        "Recipient",
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
        "LabelSpecification",
        "ShippingDocumentSpecification",
        "RateRequestTypes",
        "EdtRequestType",
        "PackageCount",
        "ShipmentOnlyFields",
        "ConfigurationData",
        "RequestedPackageLineItems",
    }

    def __init__(self, gobox_request: dict):
        origin = gobox_request["origin"]
        destination = gobox_request["destination"]

        super().__init__(
            {
                "DropoffType": DROPOFF_TYPE,
                "PackagingType": PACKAGING_TYPE,
                "PreferredCurrency": MONETARY_CURRENCY,
                # 'ShipmentAuthorizationDetail': None,
                "Shipper": Party(party_details=origin).data,
                "Recipient": Party(party_details=destination).data,
                "Origin": ContactAndAddress(party_details=origin).data,
                # 'SoldTo': None,
                "ShippingChargesPayment": Payment().data,
                # 'SpecialServicesRequested': None,
                # 'ExpressFreightDetail': None,
                # 'VariableHandlingChargeDetail': None,
                # 'BlockInsightVisibility': True,
                "LabelSpecification": LabelSpecification().data,
                "RateRequestTypes": RATE_REQUEST_TYPE,
                # 'ShipmentOnlyFields': None,
                # 'ConfigurationData': None,
            },
            optional_keys=self._optional_keys,
        )

        total_weight, num_packages, packages = FedexUtility.process_packages(
            gobox_request=gobox_request
        )

        self.add_values(
            TotalWeight=total_weight,
            PackageCount=num_packages,
            RequestedPackageLineItems=packages,
        )

        delivery_instructions = []

        if gobox_request.get("awb"):
            delivery_instructions.append(
                "Reference air waybill {}.".format(gobox_request["awb"])
            )

        if gobox_request.get("special_instructions"):
            delivery_instructions.append(gobox_request["special_instructions"])

        self.add_value("DeliveryInstructions", " ".join(delivery_instructions))

        if origin["country"] != destination["country"]:
            self.add_values(
                # CustomsClearanceDetail=CustomsClearanceDetail(destination, shipment_request['Commodities']).data,
                # ShippingDocumentSpecification=ShippingDocumentSpecification(is_international=True).data,
                EdtRequestType=ESTIMATE_DUTIES_TAXES
            )

        if gobox_request.get("pickup"):
            self.add_value(
                "PickupDetail", PickupDetail(pickup=gobox_request["pickup"]).data
            )
