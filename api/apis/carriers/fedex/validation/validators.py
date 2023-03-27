import abc
import re
from decimal import Decimal, ROUND_05UP, InvalidOperation
from typing import Any, TypeVar, Generic

FedExValidator = TypeVar("FedExValidator")


class Validator(abc.ABC, Generic[FedExValidator]):
    @classmethod
    @abc.abstractmethod
    def clean(cls, data: Any) -> Any:
        pass

    @classmethod
    @abc.abstractmethod
    def validate(cls, data: Any) -> Any:
        pass


class FedExValidationError(Exception):
    pass


class NumericValidator(Validator):
    _validation_format = (0, 9999999999999999999999999, 5)

    @classmethod
    def clean(cls, data: Any) -> Decimal:
        data = cls.validate(data)
        _, _, precision = cls._validation_format
        return data.quantize(precision, rounding=ROUND_05UP)

    @classmethod
    def validate(cls, data: Any) -> Decimal:
        if isinstance(data, (Decimal, str, int, float)):
            try:
                data = Decimal(data)
            except InvalidOperation:
                raise FedExValidationError(
                    "{} cannot be interpreted as a numeric value".format(data)
                )
        else:
            raise FedExValidationError(
                "{} of type {} cannot be interpreted as a numeric value".format(
                    data, type(data)
                )
            )

        minimum, maximum, _ = cls._validation_format
        if not minimum <= data <= maximum:
            raise FedExValidationError(
                "{} is out of bounds ({}-{})".format(data, minimum, maximum)
            )

        return data


class StringValidator(Validator):
    _validation_format = (re.compile(r".*"), -1)

    @classmethod
    def clean(cls, data: Any) -> str:
        return cls.validate(data)

    @classmethod
    def validate(cls, data: Any) -> str:
        data = str(data)[: cls._validation_format[1]]
        if not cls._validation_format[0].match(data):
            raise FedExValidationError(
                "{} does not satisfy the pattern {}".format(
                    data, cls._validation_format[0].pattern
                )
            )
        return data


class DeclaredValue(NumericValidator):
    _validation_format = (Decimal(0), Decimal("9" * 11), Decimal(2))


class FreightToCollectAmount(NumericValidator):
    _validation_format = (Decimal(0), Decimal("9" * 10), Decimal(2))


class Dimension(NumericValidator):
    _validation_format = (Decimal(1), Decimal("9" * 3), Decimal(0))


class MeterNumber(NumericValidator):
    _validation_format = (Decimal("1" * 9), Decimal("9" * 9), Decimal(0))


class Weight(NumericValidator):
    _validation_format = (Decimal(0), Decimal("9" * 8), Decimal(1))


class TrackingNumber(NumericValidator):
    _validation_format = (Decimal(1), Decimal("9" * 15), Decimal(0))


class Commodity(StringValidator):
    _validation_format = (re.compile(r".{0,450}"), 450)


class CommodityPartNumber(StringValidator):
    _validation_format = (re.compile(r".{0,20}"), 20)


class CommercialInvoiceComments(StringValidator):
    _validation_format = (re.compile(r".{0,444}"), 444)


class DeptNotes(StringValidator):
    _validation_format = (re.compile(r".{0,30}"), 30)


class AddressLine(StringValidator):
    _validation_format = (re.compile(r".{0,35}"), 35)


class City(StringValidator):
    _validation_format = (re.compile(r".{1,20}"), 20)


class PartyCode(StringValidator):
    _validation_format = (re.compile(r".{0,20}"), 20)


class Name(StringValidator):
    _validation_format = (re.compile(r".{0,35}"), 35)


class Phone(StringValidator):
    _validation_format = (re.compile(r".{1,15}"), 15)


class State(StringValidator):
    _validation_format = (re.compile(r".{2}"), 2)


class Postal(StringValidator):
    _validation_format = (re.compile(r".{1,5}"), 5)


class Reference(StringValidator):
    _validation_format = (re.compile(r".{0,35}"), 35)


class Contents(StringValidator):
    _validation_format = (re.compile(r".{0,70}"), 70)
