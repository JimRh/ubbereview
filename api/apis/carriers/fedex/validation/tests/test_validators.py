from decimal import Decimal
from django.test import TestCase

from api.apis.carriers.fedex.validation.validators import (
    StringValidator,
    Commodity,
    CommodityPartNumber,
    CommercialInvoiceComments,
    DeptNotes,
    AddressLine,
    City,
    PartyCode,
    Name,
    Phone,
    State,
    Postal,
    Reference,
    Contents,
    FedExValidationError,
    NumericValidator,
    DeclaredValue,
    FreightToCollectAmount,
    Dimension,
    MeterNumber,
    Weight,
    TrackingNumber,
)


class TestStringValidators(TestCase):
    def setUp(self):
        self.min_length = 0
        self.max_length = 1
        self.validator = StringValidator

    def runTest(self):
        min_string = "A" * self.min_length
        max_string = "A" * self.max_length
        self.assertEqual(self.min_length, len(self.validator.clean(min_string)))
        self.assertEqual(self.max_length, len(self.validator.clean(max_string)))

        min_string_extended = "A" * (self.min_length - 1)
        max_string_extended = "A" * (self.max_length + 1)
        if self.min_length:
            with self.assertRaises(FedExValidationError):
                self.validator.clean(min_string_extended)
        else:
            self.assertEqual(
                self.min_length, len(self.validator.clean(min_string_extended))
            )
        self.assertEqual(
            self.max_length, len(self.validator.clean(max_string_extended))
        )

    def test_Commodity(self):
        self.min_length = 0
        self.max_length = 450
        self.validator = Commodity
        self.runTest()

    def test_CommodityPartNumber(self):
        self.min_length = 0
        self.max_length = 20
        self.validator = CommodityPartNumber
        self.runTest()

    def test_CommercialInvoiceComments(self):
        self.min_length = 0
        self.max_length = 444
        self.validator = CommercialInvoiceComments
        self.runTest()

    def test_DeptNotes(self):
        self.min_length = 0
        self.max_length = 30
        self.validator = DeptNotes
        self.runTest()

    def test_AddressLine(self):
        self.min_length = 0
        self.max_length = 35
        self.validator = AddressLine
        self.runTest()

    def test_City(self):
        self.min_length = 1
        self.max_length = 20
        self.validator = City
        self.runTest()

    def test_PartyCode(self):
        self.min_length = 0
        self.max_length = 20
        self.validator = PartyCode
        self.runTest()

    def test_Name(self):
        self.min_length = 0
        self.max_length = 35
        self.validator = Name
        self.runTest()

    def test_Phone(self):
        self.min_length = 1
        self.max_length = 15
        self.validator = Phone
        self.runTest()

    def test_State(self):
        self.min_length = 2
        self.max_length = 2
        self.validator = State
        self.runTest()

    def test_Postal(self):
        self.min_length = 1
        self.max_length = 5
        self.validator = Postal
        self.runTest()

    def test_Reference(self):
        self.min_length = 0
        self.max_length = 35
        self.validator = Reference
        self.runTest()

    def test_Contents(self):
        self.min_length = 0
        self.max_length = 70
        self.validator = Contents
        self.runTest()


class TestNumericValidators(TestCase):
    def setUp(self):
        self.min_val = Decimal(0)
        self.max_val = Decimal(1)
        self.precision = Decimal(2)
        self.validator = NumericValidator

    def runTest(self):
        cleaned = self.validator.clean(self.min_val)
        self.assertEqual(cleaned, self.min_val)

        cleaned = self.validator.clean(self.max_val)
        self.assertEqual(cleaned, self.max_val)

        # Str
        cleaned = self.validator.clean(str(self.min_val))
        self.assertEqual(cleaned, self.min_val)

        cleaned = self.validator.clean(str(self.max_val))
        self.assertEqual(cleaned, self.max_val)

        # Float
        cleaned = self.validator.clean(float(self.min_val))
        self.assertEqual(cleaned, self.min_val)

        cleaned = self.validator.clean(float(self.max_val))
        self.assertEqual(cleaned, self.max_val)

        with self.assertRaises(FedExValidationError):
            self.validator.clean(self.min_val - 1)
        with self.assertRaises(FedExValidationError):
            self.validator.clean(self.max_val + 1)
        with self.assertRaises(FedExValidationError):
            self.validator.clean(str(self.min_val - 1))
        with self.assertRaises(FedExValidationError):
            self.validator.clean(str(self.max_val + 1))
        with self.assertRaises(FedExValidationError):
            self.validator.clean(float(self.min_val - 11))
        with self.assertRaises(FedExValidationError):
            self.validator.clean(float(self.max_val + 1))

    def test_DeclaredValue(self):
        self.min_val = Decimal(0)
        self.max_val = Decimal("9" * 11)
        self.precision = Decimal(2)
        self.validator = DeclaredValue
        self.runTest()

    def test_FreightToCollectAmount(self):
        self.min_val = Decimal(0)
        self.max_val = Decimal("9" * 10)
        self.precision = Decimal(2)
        self.validator = FreightToCollectAmount
        self.runTest()

    def test_Dimension(self):
        self.min_val = Decimal(1)
        self.max_val = Decimal("9" * 3)
        self.precision = Decimal(0)
        self.validator = Dimension
        self.runTest()

    def test_MeterNumber(self):
        self.min_val = Decimal("1" * 9)
        self.max_val = Decimal("9" * 9)
        self.precision = Decimal(0)
        self.validator = MeterNumber
        self.runTest()

    def test_Weight(self):
        self.min_val = Decimal(0)
        self.max_val = Decimal("9" * 8)
        self.precision = Decimal(1)
        self.validator = Weight
        self.runTest()

    def test_TrackingNumber(self):
        self.min_val = Decimal(1)
        self.max_val = Decimal("9" * 15)
        self.precision = Decimal(0)
        self.validator = TrackingNumber
        self.runTest()
