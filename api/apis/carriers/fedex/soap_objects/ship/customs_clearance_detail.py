from decimal import Decimal

from api.apis.carriers.fedex.globals.globals import (
    BROKER_TYPE,
    EXPORT_DOCUMENT_CONTENT,
    BROKER_SEL_TYPE,
)
from api.apis.carriers.fedex.soap_objects.common.money import Money
from api.apis.carriers.fedex.soap_objects.common.payment import Payment
from api.apis.carriers.fedex.soap_objects.ship.brokers_detail import BrokerDetail
from api.apis.carriers.fedex.soap_objects.ship.commercial_invoice import (
    CommercialInvoice,
)
from api.apis.carriers.fedex.soap_objects.rate.customs_option_detail import (
    CustomsOptionDetail,
)
from api.apis.carriers.fedex.soap_objects.rate.recipient_customs_id import (
    RecipientCustomsId,
)
from api.apis.carriers.fedex.soap_objects.ship.commodity import Commodity
from api.apis.carriers.fedex.soap_objects.ship.export_detail import ExportDetail
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class CustomsClearanceDetail(FedExSoapObject):
    _optional_keys = {
        "Brokers",
        "ClearanceBrokerage",
        "CustomsOptions",
        "ImporterOfRecord",
        "RecipientCustomsId",
        "DutiesPayment",
        "DocumentContent",
        "CustomsValue",
        "FreightOnValue",
        "InsuranceCharges",
        "PartiesToTransactionAreRelated",
        "CommercialInvoice",
        "Commodities",
        "ExportDetail",
        "RegulatoryControls",
    }

    def __init__(self, recipient: dict, commodities: list, broker: dict, origin: dict):
        processed_commodity = []
        value = Decimal("0.0")

        for commodity in commodities:
            value += Decimal(commodity["unit_value"])
            processed_commodity.append(Commodity(commodity=commodity).data)

        super().__init__(
            {
                "Brokers": BrokerDetail(
                    broker_details=broker, origin=origin, destination=recipient
                ).data,
                "ClearanceBrokerage": BROKER_SEL_TYPE,
                "CustomsOptions": CustomsOptionDetail().data,
                # 'ImporterOfRecord': None,
                "RecipientCustomsId": RecipientCustomsId(
                    recipient=recipient["company_name"]
                ).data,
                "DutiesPayment": Payment(
                    payor_information=recipient, intl_duties=True
                ).data,
                "DocumentContent": EXPORT_DOCUMENT_CONTENT,
                "CustomsValue": Money(amount=value).data,
                # 'FreightOnValue': None,
                # 'InsuranceCharges': None,
                # 'PartiesToTransactionAreRelated': None,
                "CommercialInvoice": CommercialInvoice().data,
                "Commodities": processed_commodity,
                # 'RegulatoryControls': None
            },
            optional_keys=self._optional_keys,
        )
        if recipient["country"] != "US":
            self.add_value("ExportDetail", ExportDetail().data)
