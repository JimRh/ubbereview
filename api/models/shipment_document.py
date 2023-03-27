"""
    Title: Shipment Document Model
    Description: This file will contain functions for Shipment Document Model.
    Created: June 23, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import base64
from io import BytesIO

from django.core.files import File
from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField, BooleanField
from django.db.models.fields.files import FileField
from django.db.models.fields.related import ForeignKey

from api.globals.project import LETTER_MAPPING_LEN
from api.models.base_table import BaseTable


class ShipmentDocument(BaseTable):
    """
        ShipmentDocument Model
    """

    _TYPES = (
        ("0", "Payment Receipt"),
        ("1", "Insurance Certificate"),
        ("2", "Commercial Invoice"),
        ("3", "Customs Declaration"),
        ("4", "Invoice"),  # NO customer
        ("5", "B13A"),
        ("6", "Customer Claim"),
        ("7", "DG Dec"),
        ("8", "Customer PO"),
        ("9", "BBE PO"),  # NO customer
        ("99", "Other")
    )
    shipment = ForeignKey("Shipment", on_delete=CASCADE, related_name='shipment_document_shipment')
    type = CharField(max_length=LETTER_MAPPING_LEN * 2, choices=_TYPES)
    document = FileField(upload_to='shipping_documents/%Y/%m/%d/', unique=True)
    is_bbe_only = BooleanField(default=False, help_text="Check if user is admin or not")

    class Meta:
        verbose_name = "Shipment Document"
        verbose_name_plural = "Shipment - Documents"

    @staticmethod
    def add_document(shipment, document: str, doc_type: str) -> None:
        """
            Create Shipment Document
            :param shipment: Shipment
            :param document: Document File
            :param doc_type: Docment Type
            :return: None
        """
        document = base64.b64decode(document)

        file = BytesIO()
        file.write(document)

        file = File(
            file,
            name=f"{shipment.shipment_id}-{str(doc_type)}.pdf"
        )

        new_doc = ShipmentDocument(
            shipment=shipment,
            document=file,
            type=doc_type,
        )
        new_doc.save()
        new_doc.document.close()

    # Override
    def __repr__(self) -> str:
        return f"< ShipmentDocument ({self.shipment.shipment_id}, {self.type}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.shipment.shipment_id}, {self.type}"
