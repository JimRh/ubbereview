from api.apis.carriers.fedex.globals.globals import PHYSICAL_PACKAGING_TYPE
from api.apis.carriers.fedex.soap_objects.common.customer_reference import (
    CustomerReference,
)
from api.apis.carriers.fedex.soap_objects.common.dimensions import Dimensions
from api.apis.carriers.fedex.soap_objects.common.weight import Weight
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class RequestedPackageLineItem(FedExSoapObject):
    _optional_keys = {
        "SequenceNumber",
        "GroupNumber",
        "GroupPackageCount",
        "VariableHandlingChargeDetail",
        "InsuredValue",
        "Weight",
        "Dimensions",
        "PhysicalPackaging",
        "AssociatedFreightLineItems",
        "ItemDescription",
        "ItemDescriptionForClearance",
        "CustomerReferences",
        "SpecialServicesRequested",
        "ContentRecords",
    }

    def __init__(
        self,
        package: dict,
        group_number: int = 1,
        sequence=None,
        ref_one: str = "",
        ref_two: str = "",
        order_number: str = "",
    ):
        physical_packaging = package.get("package_type", PHYSICAL_PACKAGING_TYPE)

        if physical_packaging == "BUNDLES":
            physical_packaging = PHYSICAL_PACKAGING_TYPE

        super().__init__(
            {
                # 'SequenceNumber': None,
                "GroupNumber": group_number,
                "GroupPackageCount": package.get("quantity", 1),
                "Weight": Weight(weight_value=package["weight"]).data,
                "Dimensions": Dimensions(package=package).data,
                "PhysicalPackaging": physical_packaging,
                "ItemDescription": package["description"],
                "ItemDescriptionForClearance": package["description"],
                # 'SpecialServicesRequested': None,
                # 'ContentRecords': None
            },
            optional_keys=self._optional_keys,
        )
        if sequence:
            self.add_value("SequenceNumber", sequence)

        references_list = []

        po = {"CustomerReferenceType": "P_O_NUMBER", "Value": order_number}

        references_list.append(po)

        if ref_one:
            reference = ref_one

            if ref_two:
                reference += "/" + ref_two

            references_list.append(CustomerReference(reference=reference).data)

        if references_list:
            self.add_value("CustomerReferences", references_list)

        self._weight = package["weight"]
        self._quantity = package.get("quantity", 1)

    @property
    def weight(self):
        return self._weight

    @property
    def quantity(self):
        return self._quantity
