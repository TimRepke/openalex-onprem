from typing import Type, Generator

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


def get_wrappers(keys: list[WrapperEnum] | str | None) -> Generator[Type[AnyWrapper], None, None]:
    if keys is None:
        keys = [WrapperEnum.DIMENSIONS, WrapperEnum.SCOPUS]
    if type(keys) == str:
        keys = [keys]

    for key in keys:
        yield get_wrapper(key)
