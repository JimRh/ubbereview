import abc
from abc import abstractmethod
from typing import Union


class SOAPObj(abc.ABC):
    @abstractmethod
    def _clean(self) -> None:
        pass

    @abstractmethod
    def data(self) -> Union[list, dict]:
        pass
