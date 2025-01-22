from enum import Enum
from typing import Type

from .base import AbstractWrapper
from .dimensions import DimensionsWrapper
from .scopus import ScopusWrapper

AnyWrapper = ScopusWrapper | DimensionsWrapper


class Wrapper(str, Enum):
    SCOPUS = 'scopus'
    DIMENSIONS = 'dimensions'
    WOS = 'wos'
    S2 = 's2'
    PUBMED = 'pubmed'

    @classmethod
    def list(cls) -> list[str]:
        return list(map(lambda c: c.value, cls))

    @classmethod
    def get(cls, key: 'Wrapper') -> Type[AnyWrapper]:
        if key == Wrapper.SCOPUS:
            return ScopusWrapper
        if key == Wrapper.DIMENSIONS:
            return DimensionsWrapper
