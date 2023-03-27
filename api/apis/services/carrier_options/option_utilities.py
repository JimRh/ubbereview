from datetime import datetime
from decimal import Decimal
from typing import Union

from django.core.exceptions import ObjectDoesNotExist

from api.exceptions.services import CarrierOptionException
from api.models import Carrier


def check_carrier(carrier: Union[Carrier, int]) -> Carrier:
    if isinstance(carrier, Carrier):
        return carrier

    if isinstance(carrier, int):
        try:
            return Carrier.objects.get(code=carrier)
        except ObjectDoesNotExist:
            raise CarrierOptionException({"carrier_option.carrier.value": "'carrier' must exist"})
    raise CarrierOptionException({"carrier_option.carrier.type": "'carrier' must be int or Carrier"})


def date_check(date: datetime, start_date: datetime, end_date: datetime) -> None:
    if start_date is not None and date < start_date:
        raise CarrierOptionException({"carrier_option.date.range": "'Date' is before the start date"})

    if end_date is not None and date > end_date:
        raise CarrierOptionException({"carrier_option.date.range": "'Date' is after the end date"})


def min_max_update(value: Decimal, minimum_value: Decimal, maximum_value: Decimal) -> Decimal:
    if value < minimum_value:
        value = minimum_value

    if value > maximum_value:
        value = maximum_value

    return value
