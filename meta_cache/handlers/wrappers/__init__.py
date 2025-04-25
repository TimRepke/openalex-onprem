from typing import Type

from .dimensions import DimensionsWrapper
from .scopus import ScopusWrapper
from ..wrapper import WrapperEnum

AnyWrapper = ScopusWrapper | DimensionsWrapper


def get_wrapper(key: WrapperEnum) -> Type[AnyWrapper]:
    if key == WrapperEnum.SCOPUS:
        return ScopusWrapper
    if key == WrapperEnum.DIMENSIONS:
        return DimensionsWrapper
    raise ValueError("Invalid key")
