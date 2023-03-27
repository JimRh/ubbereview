from typing import Union

from api.apis.carriers.canada_post.soap_objects.option import Option
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class Options(SOAPObj):
    def __init__(self, world_request: dict):
        self._world_request = world_request

    # Override
    def _clean(self) -> None:
        pass

    # Override
    def data(self) -> Union[list, dict]:
        if self._world_request["destination"]["country"] != "CA":
            # return [
            #     Option("RTS").data()
            # ]
            return [Option("ABAN").data()]
        return []
