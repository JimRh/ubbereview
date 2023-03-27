from decimal import Decimal
from typing import Union

from api.apis.carriers.canada_post.exceptions.exceptions import CanadaPostAPIException
from api.apis.carriers.canada_post.soap_objects.dimensions import Dimensions
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class ParcelCharacteristics(SOAPObj):
    _sigfig_precision = Decimal("0.001")
    _max_dim_threshold = Decimal("100.0")
    _min_dim_threshold = Decimal("0.0")

    def __init__(self, package: dict):
        self._weight = Decimal(package["weight"])
        self._dimensions = Dimensions(
            package["length"], package["width"], package["height"]
        )
        self._clean()

    # Override
    def _clean(self) -> None:
        if not self._min_dim_threshold < self._weight < self._max_dim_threshold:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.ParcelCharacteristics": "Package weight out of range ({} <= w <= {})".format(
                        self._min_dim_threshold, self._max_dim_threshold
                    )
                }
            )

        self._weight = self._weight.quantize(self._sigfig_precision)

    # Override
    def data(self) -> Union[list, dict]:
        return {
            "weight": self._weight,
            "dimensions": self._dimensions.data(),
            "unpackaged": False,
            "mailing-tube": False,
            "oversized": False,
        }
