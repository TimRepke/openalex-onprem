from enum import Enum
from typing import Any

from pydantic import BaseModel
from sqlalchemy import select, or_

from . import DatabaseEngine
from .schema import Record


class Query(BaseModel):
    doi: list[str] | None = None
    wos_id: list[str] | None = None
    scopus_id: list[str] | None = None
    openalex_id: list[str] | None = None
    s2_id: list[str] | None = None
    pubmed_id: list[str] | None = None
    dimensions_id: list[str] | None = None


def lookup(db_engine: DatabaseEngine, query: Query, limit: int = 100) -> list[Record]:
    with db_engine.session() as session:
        ors = []
        n_ids = 0
        for field in Query.model_fields.keys():
            if n_ids >= limit:
                raise ValueError('Requested too many ids at once!')

            ids = getattr(query, field)
            if ids is not None and len(ids) > 0:
                n_ids += len(ids)
                ors.append(getattr(Record, field).in_(ids))

        stmt = select(Record).where(or_(*ors)).limit(limit * 2)
        results = session.exec(stmt)
        return results


def register_raw(db_engine: DatabaseEngine,
                 doi: str | None = None,
                 wos_id: str | None = None,
                 scopus_id: str | None = None,
                 openalex_id: str | None = None,
                 s2_id: str | None = None,
                 pubmed_id: str | None = None,
                 dimensions_id: str | None = None,
                 s2: dict[str, Any] | None = None,
                 openalex: dict[str, Any] | None = None,
                 dimensions: dict[str, Any] | None = None,
                 scopus: dict[str, Any] | None = None,
                 wos: dict[str, Any] | None = None,
                 other: dict[str, Any] | None = None,
                 other_key: str | None = None):
    pass
