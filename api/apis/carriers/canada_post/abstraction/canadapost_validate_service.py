from decimal import Decimal
from re import fullmatch
from typing import Tuple

from zeep.exceptions import Fault

from api.apis.carriers.canada_post.abstraction.canadapost_api import CanadaPostAPI
from api.apis.carriers.canada_post.exceptions.exceptions import CanadaPostAPIException
from api.apis.carriers.canada_post.globals.util import Endpoints
from api.background_tasks.logger import CeleryLogger
from api.globals.carriers import CAN_POST


class CanadaPostValidateRate(CanadaPostAPI):
    _zero = Decimal("0.00")
    _max = Decimal("9999999999")

    def __init__(self, world_request: dict) -> None:
        super(CanadaPostValidateRate, self).__init__(world_request)
        self._canadapost_response = {}

        carrier_account = world_request["objects"]["carrier_accounts"][CAN_POST][
            "account"
        ]

        self.endpoints = Endpoints(carrier_account)

    def _clean(self):
        if len(self._world_request["service_code"]) > 13:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.ValidateService": "Service code greater than 13 characters"
                }
            )

        if (
            fullmatch(r"[A-Z]+.?[A-Z]+.?[A-Z]+", self._world_request["service_code"])
            is None
        ):
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.ValidateService": "Service code is not alphanumeric"
                }
            )

    def _is_packages_to_service_valid(self) -> bool:
        restrictions = self._canadapost_response["service"]["restrictions"]
        thousand = Decimal("1000")
        min_weight = restrictions["weight-restriction"]["min"] / thousand
        max_weight = restrictions["weight-restriction"]["max"] / thousand

        if restrictions["dimensional-restrictions"]["length"] is None:
            min_length = self._zero
            max_length = self._max
        else:
            min_length = restrictions["dimensional-restrictions"]["length"]["min"]
            max_length = restrictions["dimensional-restrictions"]["length"]["max"]

        if restrictions["dimensional-restrictions"]["width"] is None:
            min_width = self._zero
            max_width = self._max
        else:
            min_width = restrictions["dimensional-restrictions"]["width"]["min"]
            max_width = restrictions["dimensional-restrictions"]["width"]["max"]

        if restrictions["dimensional-restrictions"]["height"] is None:
            min_height = self._zero
            max_height = self._max
        else:
            min_height = restrictions["dimensional-restrictions"]["height"]["min"]
            max_height = restrictions["dimensional-restrictions"]["height"]["max"]

        length_plus_girth = restrictions["dimensional-restrictions"][
            "length-plus-girth-max"
        ]
        dim_sum_max = restrictions["dimensional-restrictions"][
            "length-height-width-sum-max"
        ]

        if not min_weight:
            min_weight = self._zero
        if not max_weight:
            max_weight = self._max
        if not length_plus_girth:
            length_plus_girth = self._max
        if not dim_sum_max:
            dim_sum_max = self._max

        for package in self._world_request["packages"]:
            weight = Decimal(package["weight"])
            length = Decimal(package["length"])
            height = Decimal(package["height"])
            width = Decimal(package["width"])

            if not min_weight <= weight <= max_weight:
                raise ValueError(
                    "Weight out of bounds ({}-{}kg)".format(min_weight, max_weight)
                )
            if not min_length <= length <= max_length:
                raise ValueError(
                    "Length out of bounds ({}-{}cm)".format(min_length, max_length)
                )
            if not min_width <= width <= max_width:
                raise ValueError(
                    "Width out of bounds ({}-{}cm)".format(min_width, max_width)
                )
            if not min_height <= height <= max_height:
                raise ValueError(
                    "Height out of bounds ({}-{}cm)".format(min_height, max_height)
                )

            if length + (2 * width) + (2 * height) > length_plus_girth:
                raise ValueError(
                    "Length plus girth (l+2w+2h) out of bounds (<={}cm)".format(
                        length_plus_girth
                    )
                )

            if length + width + height > dim_sum_max:
                raise ValueError(
                    "Sum of dimensions (l+w+h) out of bounds (<={}cm)".format(
                        dim_sum_max
                    )
                )
        return True

    def is_valid(self) -> Tuple[bool, str]:
        value = False

        try:
            self._clean()
        except CanadaPostAPIException as e:
            CeleryLogger().l_warning.delay(
                location="canadapost_validate_service line: 110",
                message=str({"api.error.canada_post.ValidateService": e.message}),
            )
            return value, ""

        try:
            self._post()
        except CanadaPostAPIException as e:
            CeleryLogger().l_warning.delay(
                location="canadapost_validate_service line: 119",
                message=str({"api.error.canada_post.ValidateService": e.message}),
            )
            return value, ""

        if self._canadapost_response["messages"] is not None:
            CeleryLogger().l_warning.delay(
                location="canadapost_validate_service line: 127",
                message="Canada Post validate return data: {}".format(
                    self._canadapost_response
                ),
            )
            return value, ""

        try:
            self._is_packages_to_service_valid()
        except ValueError as e:
            return value, str(e)
        value = True

        return value, self._canadapost_response["service"]["service-name"]

    # Override
    def _format_response(self) -> None:
        pass

    # Override
    def _post(self) -> None:
        try:
            self._canadapost_response = self.endpoints.RATE_SERVICE.GetService(
                **{
                    "service-code": self._world_request["service_code"],
                    "destination-country-code": self._world_request["destination"][
                        "country"
                    ],
                }
            )
        except Fault as e:
            CeleryLogger().l_warning.delay(
                location="canadapost_validate_service line: 152",
                message=str(
                    {
                        "api.error.canada_post.ValidateService": "Zeep Failure: {}".format(
                            e.message
                        )
                    }
                ),
            )

            raise CanadaPostAPIException(
                {"api.error.canada_post.ValidateService": "Could not validate service"}
            )
