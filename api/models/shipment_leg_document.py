"""
    Title: ShipDocument Model
    Description: This file will contain functions for ShipDocument Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import base64
from io import BytesIO

from django.core.files import File
from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField, PositiveSmallIntegerField, BooleanField
from django.db.models.fields.files import FileField
from django.db.models.fields.related import ForeignKey

from api.globals.project import LETTER_MAPPING_LEN
from api.models.base_table import BaseTable


class ShipDocument(BaseTable):
    """
        ShipDocument Model
    """

    _TYPES = (
        ("0", "Bill of Lading/Airway Bill"),
        ("1", "Cargo Label"),
        ("2", "Proof of Delivery"),
        ("3", "Proof of Pickup"),
        ("4", "Weight & Inspection Certificate"),
        ("5", "Claim"),  # NO customer
        ("6", "Invoice"),  # NO customer
        ("7", "Marine Form"),
        ("99", "Other")  # NO customer
    )
    leg = ForeignKey("Leg", on_delete=CASCADE, related_name='shipdocument_leg')
    # TODO: DEPRECATE
    type = PositiveSmallIntegerField(default=0)
    new_type = CharField(max_length=LETTER_MAPPING_LEN * 2, choices=_TYPES)
    document = FileField(upload_to='shipping_documents/%Y/%m/%d/', unique=True)
    is_bbe_only = BooleanField(default=False, help_text="Check if user is admin or not")

    class Meta:
        verbose_name = "Leg Document"
        verbose_name_plural = "Leg - Documents"

    @staticmethod
    def add_document(leg, document: str, doc_type: int) -> None:
        """
            Create leg Document
            :param leg: Leg
            :param document: Document File
            :param doc_type: Docment Type
            :return: None
        """
        document = base64.b64decode(document)

        file = BytesIO()
        file.write(document)

        file = File(
            file,
            name=f"{leg.leg_id}-{str(doc_type)}.pdf"
        )

        new_doc = ShipDocument(
            leg=leg,
            document=file,
            type=doc_type,
            new_type=doc_type
        )
        new_doc.save()
        new_doc.document.close()

    # Override
    def __repr__(self) -> str:
        return f"< ShipDocument ({self.leg.leg_id}, {self.type}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.leg.leg_id}, {self.type}"
