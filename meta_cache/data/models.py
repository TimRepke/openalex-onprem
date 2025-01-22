from pydantic import BaseModel

from meta_cache.data import Record
from meta_cache.wrappers import Wrapper


class Query(BaseModel):
    openalex_id: list[str] | None = None
    doi: list[str] | None = None
    dimensions_id: list[str] | None = None
    pubmed_id: list[str] | None = None
    s2_id: list[str] | None = None
    scopus_id: list[str] | None = None
    wos_id: list[str] | None = None


class Request(Query):
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

    # Wrapper to use for external API request
    wrapper: Wrapper = Wrapper.SCOPUS

    # Limit the number of requested entries (leave at default unless you absolutely know what you are doing)
    limit: int = 100

    @property
    # Query contains DOIs
    def has_doi(self) -> bool:
        return self.doi is not None and len(self.doi) > 0

    @property
    # Query contains OpenAlex IDs
    def has_oa(self) -> bool:
        return self.openalex_id is not None and len(self.openalex_id) > 0

    @property
    # Dict lookup DOI -> OpenAlex ID
    def doi_oa_map(self) -> dict[str, str]:
        return {
            doi: oa
            for oa, doi in zip(self.openalex_id, self.doi)
        } if self.has_doi and self.has_oa else {}

    @property
    # Dict lookup OpenAlex ID -> DOI
    def oa_doi_map(self) -> dict[str, str]:
        return {
            oa: doi
            for oa, doi in zip(self.openalex_id, self.doi)
        } if self.has_doi and self.has_oa else {}

    @property
    # True iff we may need to contact API wrapper
    def use_wrapper(self):
        return (self.fetch_on_previous_try
                or self.fetch_on_missing_raw
                or self.fetch_on_missing_abstract
                or self.fetch_on_previous_try)

    # List of IDs for key (e.g. scopus_id) or None
    def ids(self, key: str | None = None) -> list[str] | None:
        return getattr(self, key) if key is not None else None

    # Query has IDs for key (e.g. scopus_id)
    def has_ids(self, key: str | None) -> bool:
        return self.ids(key) is not None and len(self.ids(key)) > 0

    # Dict lookup IDs for key -> OpenAlex ID
    def id_oa_map(self, key: str | None) -> dict[str, str]:
        return {
            kid: oa
            for oa, kid in zip(self.openalex_id, self.ids(key))
        } if self.has_ids(key) and self.has_oa else {}

    # Dict lookup OpenAlex ID -> IDs for key
    def oa_id_map(self, key: str | None) -> dict[str, str]:
        return {
            oa: kid
            for oa, kid in zip(self.openalex_id, self.ids(key))
        } if self.has_ids(key) and self.has_oa else {}

    # All list of DOIs has same length as list of OpenAlex IDs (optionally also check with IDs for key)
    def is_valid_request(self, key: str | None) -> bool:
        return (
                self.has_oa and (
                (self.has_doi and self.has_ids(key)
                 and (len(self.doi) == len(self.openalex_id))
                 and (len(self.ids(key)) == len(self.openalex_id))) or
                (self.has_doi and not self.has_ids and (len(self.doi) == len(self.openalex_id))) or
                (not self.has_doi and self.has_ids and (len(self.ids(key)) == len(self.openalex_id)))
        ))


class Response(Query):
    found: list[Record]
    updated: Query | None = None
    queued: Query | None = None
    missed: Query | None = None
    queue_job_id: str | None = None
