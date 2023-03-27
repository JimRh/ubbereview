"""
    Title: Dangerous Good Classification Model
    Description: This file will contain functions for Dangerous Good Classification Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.core.exceptions import ValidationError
from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField, PositiveSmallIntegerField
from django.db.models.fields.related import OneToOneField

from api.globals.project import DEFAULT_CHAR_LEN, MAX_CHAR_LEN
from api.models import DangerousGoodPlacard
from api.models.base_table import BaseTable


class DangerousGoodClassification(BaseTable):
    """
        DangerousGoodClassification Model
    """

    classification = PositiveSmallIntegerField()
    division = PositiveSmallIntegerField()
    class_name = CharField(max_length=DEFAULT_CHAR_LEN)
    division_characteristics = CharField(max_length=MAX_CHAR_LEN, unique=True)
    label = OneToOneField(
        DangerousGoodPlacard, on_delete=CASCADE, related_name="dangerousgoodclassification_dangerousgoodlabel"
    )

    class Meta:
        verbose_name = "Dangerous Good Classification"
        ordering = ["classification", "division"]

    @staticmethod
    def to_tuple() -> tuple:
        """
            Get Classification information for dropdown
            :return: tuple of all Classifications
        """

        ret=[]
        for classification in DangerousGoodClassification.objects.all():
            ret.append((classification.id, str(classification)))
        return tuple(ret)

    def verbose_classification(self) -> str:
        """
            Get the verbose full Classification name
            :return: str
        """

        if self.division:
            return str(self.classification) + "." + str(self.division)
        return str(self.classification)

    # Override
    def clean(self) -> None:
        if self.classification > 9 or self.classification < 1:
            raise ValidationError("Field 'classification' must be from 1 to 9 inclusive")

        if self.division > 6 or self.division < 0:
            raise ValidationError("Field 'division' must be from 0 to 6 inclusive")

    # Override
    def save(self, *args, **kwargs) -> None:
        self.clean_fields()
        self.clean()
        self.validate_unique()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< DangerousGoodClassification ({self.classification}.{self.division}: {self.class_name}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.classification}.{self.division}: {self.class_name}"
