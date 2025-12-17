from abc import ABCMeta
from typing import Type, Generator

from .dimensions import DimensionsWrapper
from .scopus import ScopusWrapper
from .pubmed import PubmedWrapper
from ..wrapper import WrapperEnum

AnyWrapper = ScopusWrapper | DimensionsWrapper | PubmedWrapper


def get_wrapper(key: WrapperEnum) -> Type[AnyWrapper]:
    if key == WrapperEnum.SCOPUS:
        return ScopusWrapper
    if key == WrapperEnum.DIMENSIONS:
        return DimensionsWrapper
    if key == WrapperEnum.PUBMED:
        return PubmedWrapper
    raise ValueError("Invalid key")


def get_wrappers(keys: list[WrapperEnum] | str | None = None) -> Generator[Type[AnyWrapper], None, None]:
    if keys is None:
        keys = [WrapperEnum.DIMENSIONS, WrapperEnum.SCOPUS, WrapperEnum.PUBMED]

    if type(keys) == str or type(keys) == ABCMeta:
        keys = [keys]

    for key in keys:
        yield get_wrapper(key)
