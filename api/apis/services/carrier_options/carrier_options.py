import datetime
from decimal import Decimal
from typing import Union, List

import numexpr

from api.apis.services.carrier_options.option_utilities import check_carrier, date_check, min_max_update
from api.exceptions.services import CarrierOptionException
from api.general.convert import Convert
from api.models import Carrier, CarrierOption


class CarrierOptions:

    @staticmethod
    def check_carrier_has_options(carrier: int, options: List[int]) -> bool:

        carrier_options = CarrierOption.objects.select_related(
            "carrier"
        ).filter(carrier__code=carrier, option__id__in=options)

        if not carrier_options:
            return False
        return carrier_options.count() == len(options)

    @staticmethod
    def get_calculated_option_costs(carrier: Union[Carrier, int], options: list, actual: Decimal, cubic: Decimal,
                                    freight: Decimal, date: datetime.datetime) -> List[dict]:
        if not options:
            return []
        carrier = check_carrier(carrier)
        dimensional = float(cubic * carrier.linear_weight)
        actual = float(Convert().kgs_to_lbs(actual))
        weight = max(dimensional, actual)  # pylint: disable=unused-variable
        freight = float(freight)  # pylint: disable=unused-variable
        carrier_options = CarrierOption.objects.filter(carrier=carrier, option_id__in=options)

        if not carrier_options:
            raise CarrierOptionException({"carrier_option.carrier.content": "'" + carrier.name + "' has no options"})
        processed_carrier_options = []

        for option in carrier_options:
            date_check(date, option.start_date, option.end_date)
            value = Decimal(numexpr.evaluate(option.evaluation_expression).item()).quantize(Decimal("0.01"))
            processed_carrier_options.append({
                "name": option.option.name,
                "cost": min_max_update(value, option.minimum_value, option.maximum_value),
                "percentage": option.percentage
            })

        return processed_carrier_options
