from collections import defaultdict
from typing import Any, Iterable, Generator

from sqlalchemy import select, or_
import pandas as pd

from .db import DatabaseEngine
from .models import Query, Response, Request
from .schema import Record
from meta_cache.wrappers import Wrapper


class ResponseTracker:
    def __init__(self, query: Query | Request):
        if isinstance(query, Query):
            query = Request(**query.model_dump())
        self.request: Request = query

        self.df = pd.DataFrame({
            **query.model_dump(include=set(Query.model_fields.keys())),
            'missed': None,
            'updated': None,
            'queued': None,
        })
        self.id_field: str | None = None
        self.ors = []
        self.n_ids = self.df.notna().to_numpy().sum()

        for field in Query.model_fields.keys():
            ids = getattr(query, field)
            if ids is not None and len(ids) > 0:
                self.n_ids += len(ids)
                self.ors.append(getattr(Record, field).in_(ids))

    @property
    def id_oa_map(self):
        if not self.id_field:
            return {}
        return self.request.id_oa_map(self.id_field)

    @property
    def oa_id_map(self):
        if not self.id_field:
            return {}
        return self.request.oa_id_map(self.id_field)

    def get_response(self, results: list[Record]) -> Response:
        return Response(
            found=results,
            missed=Query(**self.missed),
            queued=Query(**self.queued),
            updated=Query(**self.updated),
        )

    def mark_seen(self, records: Iterable[Record]) -> None:
        for record in records:
            for field in self.missed.keys():
                if getattr(record, field) is not None:
                    self.missed[field].discard(getattr(record, field))

    def mark_updated(self, field: str, value: str) -> None:
        self.updated[field].add(value)

    def mark_queued(self, field: str, ids: list[str] | None = None, value: str | None = None) -> None:
        if ids is not None:
            self.queued[field].update(ids)
        elif value is not None:
            self.queued[field].add(value)


def lookup(db_engine: DatabaseEngine,
           query: Query | None = None,
           response_tracker: ResponseTracker | None = None) -> Generator[Record, None, None]:
    if query is None and response_tracker is None:
        raise AttributeError('You must specify a `query` or `response_tracker`')
    if response_tracker is None:
        response_tracker = ResponseTracker(query=query)
    with db_engine.session() as session:
        stmt = (select(Record)
                .where(or_(*response_tracker.ors))
                .limit(response_tracker.n_ids * 2))
        yield from session.exec(stmt)


def fix_links(db_engine: DatabaseEngine,
              results: Iterable[Record],
              response_tracker: ResponseTracker) -> Iterable[Record]:
    doi_oa_map = response_tracker.request.doi_oa_map
    oa_doi_map = response_tracker.request.oa_doi_map
    id_oa_map = response_tracker.id_oa_map
    oa_id_map = response_tracker.oa_id_map

    with db_engine.session() as session:
        for record in results:
            if record.doi in doi_oa_map and record.openalex_id is None:
                record.openalex_id = doi_oa_map[record.doi]
                response_tracker.mark_updated('openalex_id', record.openalex_id)
                response_tracker.mark_updated('doi', record.doi)
            elif record.openalex_id in oa_doi_map and record.doi is None:
                record.doi = oa_doi_map[record.openalex_id]
                response_tracker.mark_updated('openalex_id', record.openalex_id)
                response_tracker.mark_updated('doi', record.doi)

            if (record.openalex_id in oa_id_map and
                    response_tracker.id_field and
                    getattr(record, response_tracker.id_field) is None):
                setattr(record, response_tracker.id_field, oa_id_map[record.openalex_id])
                response_tracker.mark_updated('openalex_id', record.openalex_id)
                response_tracker.mark_updated(response_tracker.id_field, getattr(record, response_tracker.id_field))
            elif (response_tracker.id_field and
                  getattr(record, response_tracker.id_field) in id_oa_map and
                  record.openalex_id is None):
                record.openalex_id = id_oa_map[getattr(record, response_tracker.id_field)]
                response_tracker.mark_updated('openalex_id', record.openalex_id)
                response_tracker.mark_updated(response_tracker.id_field, getattr(record, response_tracker.id_field))

            session.add(record)
            session.commit()

            yield record


def fetch(db_engine: DatabaseEngine, request: Request) -> Response:
    response_tracker = ResponseTracker(query=request)

    if response_tracker.n_ids >= request.limit:
        raise ValueError('Requested too many ids at once!')

    # Fetch from database based on all IDs
    results = list(lookup(db_engine=db_engine, response_tracker=response_tracker))
    response_tracker.mark_seen(results)

    if request.use_wrapper:
        # Get requested API wrapper
        wrapper = Wrapper.get(request.wrapper)
        response_tracker.id_field = wrapper.db_field_id

        if not request.is_valid_request(wrapper.db_field_id):
            raise ValueError('Invalid request!')

        # Prepare list for wrapper request: Missing entries via `fetch_on_missing_entry`
        if request.fetch_on_missing_entry:
            for field, ids in response_tracker.missed:
                response_tracker.mark_queued(field, ids=ids)

        for record in results:
            if ((
                    # Prepare list for wrapper request: Existing entries w/o abstract via `fetch_on_missing_abstract`
                    (request.fetch_on_missing_abstract and record.abstract is None) or
                    # Prepare list for wrapper request: Existing entries w/o wrapper raw data via `fetch_on_missing_raw`
                    (request.fetch_on_missing_raw and getattr(record, wrapper.db_field_raw) is None)
            ) and (
                    # Only run fetch again if wrapper is forced, or we haven't tried before with this wrapper
                    request.fetch_on_previous_try or
                    not request.fetch_on_previous_try and (
                            getattr(record, wrapper.db_field_requested) is None or
                            getattr(record, wrapper.db_field_requested) is False))
            ):
                for field in wrapper.db_id_fields:
                    response_tracker.mark_queued(field, value=getattr(record, field))

    if request.update_links:
        results = list(fix_links(db_engine=db_engine, results=results, response_tracker=response_tracker))

    return response_tracker.get_response(results=results)

    # .enqueue(count_words_at_url, 'http://nvie.com')



# for doi in dois:
#     yield Record(
#         doi=doi,
#         time_scopus=datetime.now(),
#         requested_scopus=False,
#     )
#
# for scopus_id in scopus_ids:
#     yield Record(
#         scopus_id=scopus_id,
#         time_scopus=datetime.now(),
#         requested_scopus=False,
#     )


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
