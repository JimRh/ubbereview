from decimal import Decimal
from typing import Union

from api.apis.carriers.canada_post.exceptions.exceptions import CanadaPostAPIException
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class Dimensions(SOAPObj):
    _sigfig_precision = Decimal("0.1")
    _max_dim_threshold = Decimal("1000.0")
    _min_dim_threshold = Decimal("0.0")

    def __init__(self, length: str, width: str, height: str) -> None:
        self._length = Decimal(length)
        self._width = Decimal(width)
        self._height = Decimal(height)
        self._clean()

    # Override
    def _clean(self) -> None:
        if not self._min_dim_threshold < self._length < self._max_dim_threshold:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.Dimensions": "Package length out of range ({} <= l <= {})".format(
                        self._min_dim_threshold, self._max_dim_threshold
                    )
                }
            )

        if not self._min_dim_threshold < self._width < self._max_dim_threshold:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.Dimensions": "Package width out of range ({} <= w <= {})".format(
                        self._min_dim_threshold, self._max_dim_threshold
                    )
                }
            )

        if not self._min_dim_threshold < self._height < self._max_dim_threshold:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.Dimensions": "Package height out of range ({} <= h <= {})".format(
                        self._min_dim_threshold, self._max_dim_threshold
                    )
                }
            )

        self._length = self._length.quantize(self._sigfig_precision)
        self._width = self._width.quantize(self._sigfig_precision)
        self._height = self._height.quantize(self._sigfig_precision)

    # Override
    def data(self) -> Union[list, dict]:
        return {"length": self._length, "width": self._width, "height": self._height}
