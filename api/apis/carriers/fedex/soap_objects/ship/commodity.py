from decimal import Decimal

from api.apis.carriers.fedex.globals.globals import PURPOSE_OF_SHIPMENT
from api.apis.carriers.fedex.soap_objects.common.money import Money
from api.apis.carriers.fedex.soap_objects.common.weight import Weight
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject
from api.apis.carriers.fedex.validation import validators


class Commodity(FedExSoapObject):
    _required_keys = {
        "NumberOfPieces",
        "CountryOfManufacture",
    }
    _optional_keys = {
        "Name",
        "Description",
        "Purpose",
        "HarmonizedCode",
        "Weight",
        "Quantity",
        "QuantityUnits",
        "AdditionalMeasures",
        "UnitPrice",
        "CustomsValue",
        "ExciseConditions",
        "ExportLicenseNumber",
        "ExportLicenseExpirationDate",
        "CIMarksAndNumbers",
        "PartNumber",
        "NaftaDetail",
    }
    _validators = {
        "Name": validators.Name,
        "Description": validators.Contents,
        "Weight": validators.Weight,
    }

    def __init__(self, commodity: dict):
        super().__init__(
            {
                "Description": commodity["description"] + commodity["description"],
                "Purpose": PURPOSE_OF_SHIPMENT,
                "CountryOfManufacture": commodity["made_in_country_code"],
                # 'HarmonizedCode': None,
                "Weight": Weight(weight_value=commodity["total_weight"]).data,
                "NumberOfPieces": commodity["quantity"],
                "Quantity": commodity["quantity"],
                "QuantityUnits": "EA",
                # 'AdditionalMeasures': None,
                "UnitPrice": Money(
                    amount=Decimal(commodity["unit_value"])
                    / Decimal(commodity["quantity"])
                ).data,
                "CustomsValue": Money(amount=Decimal(commodity["unit_value"])).data,
                # 'ExciseConditions': None,
                # 'ExportLicenseNumber': None,
                # 'ExportLicenseExpirationDate': None,
                # 'CIMarksAndNumbers': None,
                # 'PartNumber': None,
                # 'NaftaDetail': None
            },
            optional_keys=self._optional_keys,
            required_keys=self._required_keys,
            validators=self._validators,
        )
