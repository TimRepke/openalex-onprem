from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel
from sqlalchemy import select

from meta_cache.data import Record, DatabaseEngine, ApiKey
from meta_cache.data.crud import Query


class Wrapper(Enum, str):
    SCOPUS = 'scopus'
    WOS = 'wos'
    S2 = 's2'
    DIMENSIONS = 'dimensions'


class Request(Query):
    lookup_only: bool = True
    source: Wrapper = Wrapper.SCOPUS


def request() -> list[Record]:
    if preferred_wrapper == Wrapper.SCOPUS or scopus_id is not None:
        pass

    pass
