from enum import Enum
from typing import Type


class WrapperEnum(str, Enum):
    SCOPUS = 'scopus'
    DIMENSIONS = 'dimensions'
    WOS = 'wos'
    S2 = 's2'
    PUBMED = 'pubmed'

    @classmethod
    def list(cls) -> list[str]:
        return list(map(lambda c: c.value, cls))

    @classmethod
    def queue_name(cls, wrapper: str) -> str:
        return f'meta-cache-{wrapper}'
