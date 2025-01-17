from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from meta_cache.data import Record, DatabaseEngine, ApiKey
from meta_cache.data.crud import Query

class Wrapper(Enum, str):
    SCOPUS = 'scopus'
    WOS = 'wos'
    S2 = 's2'
    DIMENSIONS = 'dimensions'


class Request(Query):
    preferred_wrapper: Wrapper = Wrapper.SCOPUS

def get(obj: dict[str, Any], *keys, default: Any = None) -> Any | None:
    for key in keys:
        obj = obj.get(key)
        if obj is None:
            return default
    return obj
class AbstractWrapper(ABC):
    @staticmethod
    @abstractmethod
    def get_title(obj: dict[str, Any]) -> str | None:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def get_abstract(obj: dict[str, Any]) -> str | None:
        raise NotImplementedError()
    @staticmethod
    @abstractmethod
    def get_doi(obj: dict[str, Any]) -> str | None:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def get_api_key(db_engine: DatabaseEngine) -> ApiKey | None:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def fetch(db_engine: DatabaseEngine, query: Query) -> None:
        raise NotImplementedError()


def request() -> list[Record]:
    if preferred_wrapper == Wrapper.SCOPUS or scopus_id is not None:
        pass

    pass
