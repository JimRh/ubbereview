from api.apis.carriers.fedex.soap_objects.common.party import Party
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class BrokerDetail(FedExSoapObject):
    _optional_keys = {"Type", "Broker"}

    def __init__(self, broker_details: dict, origin: dict, destination: dict):
        if destination["country"] == "CA" and origin["country"] != "CA":
            broker_type = "IMPORT"
        else:
            # origin["country"] == "CA" and destination["country"] != "CA":
            broker_type = "EXPORT"

        super().__init__(
            {
                "Broker": Party(party_details=broker_details).data,
                "Type": "IMPORT",
            },
            optional_keys=self._optional_keys,
        )
