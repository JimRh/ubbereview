import abc
import copy
from abc import abstractmethod


class CanadaPostAPI(abc.ABC):
    _default_transit = 10

    def __init__(self, world_request: dict) -> None:
        self._world_request = world_request
        self._canadapost_request = {}

        copied = copy.deepcopy(world_request)

        if "dg_service" in copied:
            del copied["dg_service"]

        if "objects" in copied:
            del copied["objects"]

        self._error_world_request = copied

    @abstractmethod
    def _format_response(self) -> None:
        pass

    @abstractmethod
    def _post(self) -> None:
        pass
