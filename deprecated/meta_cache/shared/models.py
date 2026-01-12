import uuid
from typing import Generator, Type

from pydantic import BaseModel

from .wrapper import WrapperEnum
from .schema import Request


class Reference(BaseModel):
    openalex_id: str | None = None
    doi: str | None = None
    dimensions_id: str | None = None
    pubmed_id: str | None = None
    s2_id: str | None = None
    scopus_id: str | None = None
    wos_id: str | None = None

    @classmethod
    def keys(cls) -> list[str]:
        return list(cls.model_fields.keys())

    @classmethod
    # # Record | 'Reference' | 'DehydratedRecord' | 'ResponseRecord'
    def ids(cls, reference: object) -> Generator[tuple[str, str], None, None]:
        for field in cls.keys():
            if hasattr(reference, field) and getattr(reference, field) is not None:
                yield field, getattr(reference, field)


class DehydratedRecord(Reference):
    record_id: uuid.UUID | str | None = None
    title: str | None = None
    abstract: str | None = None


class ResponseRecord(DehydratedRecord):
    queued: bool | None = None
    missed: bool | None = None
    added: bool | None = None


class CacheResponse(BaseModel):
    references: list[ResponseRecord]
    records: list[Request] | None = None
    n_hits: int
    n_queued: int
    n_missed: int
    n_added: int
    queue_job_id: str | None = None


class CacheRequest(BaseModel):
    references: list[Reference]

    # If true, will consider matching entries with empty abstract as missing record
    empty_abstract_as_missing: bool = False

    # If true, will update existing entry with previously unknown ID overlap
    update_links: bool = False

    # If true, contact wrapper API if no matching entry is in the cache
    fetch_on_missing_entry: bool = False
    # If true, contact wrapper API if abstract is empty (exception: tried before)
    fetch_on_missing_abstract: bool = False
    # If true, contact wrapper API if respective raw field is empty (exception: tried before)
    fetch_on_missing_raw: bool = False
    # If true, contact wrapper API in any case
    fetch_on_previous_try: bool = False
    # If true, returning only one result per openalex_id (which is a combination of all available records)
    collapsed: bool = False

    # Wrapper to use for external API request
    wrapper: WrapperEnum | None = None

    # If true, will return full result set instead of just dehydrated records
    include_full_records: bool = False

    # Limit the number of requested entries (leave at default unless you absolutely know what you are doing)
    limit: int = 100

    def wrappers(self) -> Generator[Type['AnyWrapper'], None, None]:
        from meta_cache.handlers.wrappers import get_wrapper, ScopusWrapper, DimensionsWrapper

        if self.wrapper:
            yield get_wrapper(self.wrapper)
        else:
            yield ScopusWrapper
            yield DimensionsWrapper
