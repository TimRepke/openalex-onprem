import logging
from typing import Iterable, Generator

from sqlmodel import select, or_
from sqlalchemy.sql._typing import _ColumnExpressionArgument

from .db import DatabaseEngine
from .models import CacheResponse, CacheRequest, ResponseRecord, Reference
from .schema import Record
from .util import get_reference_df, mark_status
from .wrappers import get_wrapper

logger = logging.getLogger('server.crud')


class CacheResponseHandler:
    def __init__(self, request: CacheRequest, db_engine: DatabaseEngine):
        self.db_engine = db_engine
        self.request = request

        # DataFrame from base fields (reference IDs)
        self.df = get_reference_df(self.request.references)

        # List of matching records from the database
        self.results: list[Record] = []

        # In case we triggered a queue job, keep track of it here
        self.queued_job: str | None = None

    @property
    # True, iff we may need to contact API wrapper
    def fetch_on_missing(self):
        return (self.request.fetch_on_previous_try
                or self.request.fetch_on_missing_raw
                or self.request.fetch_on_missing_abstract
                or self.request.fetch_on_missing_entry)

    @property
    def response(self) -> CacheResponse:
        return CacheResponse(
            references=[ResponseRecord(**rec) for rec in self.df.to_dict(orient='records')],
            records=self.results if self.request.include_full_records else None,
            n_hits=self.df['hit'].sum(),
            n_updated=self.df['updated'].sum(),
            n_queued=self.df['queued'].sum(),
            n_missed=self.df['missed'].sum(),
            n_added=0,
            queue_job_id=self.queued_job
        )

    @property
    def n_ids(self) -> int:
        return self.df.notna().to_numpy().sum()

    @property
    def ors(self) -> Generator[_ColumnExpressionArgument[bool], None, None]:
        for reference in self.request.references:
            for field, value in Reference.ids(reference):
                yield getattr(Record, field) == value

    def is_valid_request(self, key: str | None) -> bool:
        # check that rows sum to >=2 for columns [doi, openalex_id, {key}]
        keys = ['openalex_id', 'doi'] + ([] if key is None else [key])
        return all(self.df[keys].notna().sum(axis=1) > 1)

    def mark_hit(self, records: Iterable[Record]) -> None:
        for record in records:
            for field, value in Reference.ids(record):
                self.df.loc[self.df[field] == value, 'hit'] = True
                self.df.loc[self.df[field] == value, 'missed'] = None

    def mark_updated(self, field: str, value: str) -> None:
        self.df.loc[self.df[field] == value, 'updated'] = True

    def mark_queued(self, field: str, value: str) -> None:
        self.df.loc[self.df[field] == value, 'queued'] = True

    def lookup(self) -> Generator[Record, None, None]:
        with self.db_engine.session() as session:
            stmt = (select(Record)
                    .where(or_(*self.ors))
                    .limit(self.n_ids * 2))  # add limit just to be safe

            for record in session.exec(stmt):
                mark_status(self.df,
                            record,
                            status='missed' if self.request.empty_abstract_as_missing and record.abstract is None else 'hit')

                if self.request.update_links:
                    updated = False
                    for field, value in Reference.ids(record):
                        for row, ref in self.df[self.df[field] == value].iterrows():
                            for ref_field in Reference.keys():
                                if ref[ref_field] is not None and getattr(record, ref_field) is None:
                                    setattr(record, ref_field, ref[ref_field])
                                    self.df.loc[row, 'updated'] = True
                                    updated = True

                    if updated:
                        session.add(record)
                        session.commit()
                        session.refresh(record)

                yield Record.model_validate(record)

    @property
    def missed(self) -> Generator[Reference, None, None]:
        for _, reference in self.df[self.df['missed'] == True].iterrows():
            yield Reference(**reference)

    @property
    def queued(self) -> Generator[Reference, None, None]:
        for _, reference in self.df[self.df['queued'] == True].iterrows():
            yield Reference(**reference)

    def fetch(self) -> None:
        if self.n_ids >= self.request.limit:
            raise ValueError('Requested too many ids at once!')

        # Fetch from database based on all IDs and update ID references in database if necessary
        results = list(self.lookup())

        if self.fetch_on_missing:
            wrapper = get_wrapper(self.request.wrapper)
            if not self.is_valid_request(wrapper.db_field_id):
                raise ValueError('Invalid request!')

            # Prepare list for wrapper request: Missing entries via `fetch_on_missing_entry`
            if self.request.fetch_on_missing_entry:
                self.df.loc[self.df['missed'] == True, 'queued'] = True

            for record in results:
                if ((
                        # Prepare list for wrapper request: Existing entries w/o abstract via `fetch_on_missing_abstract`
                        (self.request.fetch_on_missing_abstract and record.abstract is None) or
                        # Prepare list for wrapper request: Existing entries w/o wrapper raw data via `fetch_on_missing_raw`
                        (self.request.fetch_on_missing_raw and getattr(record, wrapper.db_field_raw) is None)
                ) and (
                        # Only run fetch again if wrapper is forced, or we haven't tried before with this wrapper
                        self.request.fetch_on_previous_try or
                        not self.request.fetch_on_previous_try and (
                                getattr(record, wrapper.db_field_requested) is None or
                                getattr(record, wrapper.db_field_requested) is False))
                ):
                    for field, value in Reference.ids(record):
                        self.df.loc[self.df[field] == value, 'queued'] = True


def run_request(request: CacheRequest, db_engine: DatabaseEngine, auth_key: str) -> CacheResponse:
    handler = CacheResponseHandler(request=request, db_engine=db_engine)
    handler.fetch()
    wrapper = get_wrapper(handler.request.wrapper)
    return wrapper.run(db_engine=db_engine,
                       references=list(handler.missed),
                       auth_key=auth_key)
