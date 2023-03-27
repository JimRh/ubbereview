from typing import Union

from api.apis.carriers.canada_post.soap_objects.item import Item
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class Items(SOAPObj):
    # Override
    def _clean(self) -> None:
        pass

    # Override
    def data(self) -> Union[list, dict]:
        # For each item, add an item object
        # items = []
        return [Item().data()]
