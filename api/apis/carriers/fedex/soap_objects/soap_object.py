from decimal import Decimal
from typing import Set, Any, Dict
from zeep import xsd

from api.apis.carriers.fedex.validation.validators import (
    FedExValidator,
    FedExValidationError,
)


class FedExSoapObject:
    def __init__(
        self,
        initial_data=None,
        required_keys: Set[str] = None,
        optional_keys: Set[str] = None,
        validators: Dict[str, FedExValidator] = None,
    ):
        super().__init__()
        self._data = {}
        if isinstance(initial_data, dict):
            self.add_values(initial_data)

        if not required_keys:
            required_keys = set()
        if not optional_keys:
            optional_keys = set()
        if not validators:
            validators = {}

        self._required_keys = required_keys
        self._optional_keys = optional_keys
        self._validators = validators

    @property
    def all_keys(self):
        return self._required_keys.union(self._optional_keys)

    @property
    def raw_data(self):
        return self._data

    @property
    def data(self):
        self.validate_data()
        # if self._data_type:
        #     data = {}
        #     for k in self.all_keys:
        #         data[k] = self._data.get(k, xsd.SkipValue)
        #     LOGGER.debug(type(self._data_type(**data)))
        #     return self._data_type(**data)
        data = {}
        for k in self.all_keys:
            data[k] = self._data.get(k, xsd.SkipValue)
        return data

    def add_value(self, key: str, value: Any) -> None:
        if value is not None and not (isinstance(value, str) and value == ""):
            self._data[key] = value
        # self._data[key] = value

    def add_values(self, values: Dict[str, Any] = None, **kwargs) -> None:
        if not values:
            values = {}
        values.update(kwargs)
        for k, v in values.items():
            self.add_value(k, v)

    def validate_data(self):
        difference = self._required_keys.difference(self._data.keys())
        if difference:
            raise KeyError("Missing required key: {}".format(",".join(difference)))

        difference = set(self._data.keys()).difference(
            self._required_keys.union(self._optional_keys)
        )
        if difference:
            raise KeyError("Extra key supplied: {}".format(",".join(difference)))

        errors = {}
        for key, validator in self._validators.items():
            if key in self._data:
                value = self._data[key]
                if not isinstance(value, (str, int, float, Decimal)):
                    continue
                try:
                    validator.clean(value)
                except FedExValidationError as err:
                    errors[key] = str(err)
        if errors:
            raise FedExValidationError(errors)
