import logging
from datetime import datetime
from typing import Any, Generator

import httpx
from sqlalchemy import select, desc
from sqlmodel import Session

from meta_cache.data import DatabaseEngine
from meta_cache.data.crud import Query
from meta_cache.data.schema import ApiKey, Record, AuthApiKeyLink
from meta_cache.data.util import get
from .base import AbstractWrapper

logger = logging.getLogger('wrapper-scopus')
PAGE_SIZE = 25


class ScopusWrapper(AbstractWrapper):
    name = 'scopus'
    db_field_id = 'scopus_id'
    db_field_raw = 'raw_scopus'
    db_field_time = 'time_scopus'
    db_field_requested = 'requested_scopus'

    @staticmethod
    def get_title(obj: dict[str, Any]) -> str | None:
        return obj.get('dc:title')

    @staticmethod
    def get_abstract(obj: dict[str, Any]) -> str | None:
        return obj.get('dc:description')

    @staticmethod
    def get_doi(obj: dict[str, Any]) -> str | None:
        return obj.get('prism:doi')

    @staticmethod
    def get_id(obj: dict[str, Any]) -> str | None:
        return obj.get('eid')

    @staticmethod
    def _api_key_query_extra() -> str:
        return 'AND (api_key.scopus_requests_remaining IS NULL OR api_key.scopus_requests_remaining > 0)'

    @classmethod
    def fetch(cls, db_engine: DatabaseEngine, query: Query, auth_key: str) -> Generator[Record, None, None]:
        parts = []
        if query.scopus_id:
            parts += [f'EID({sid})' for sid in set(query.scopus_id)]
        if query.doi:
            parts += [f'DOI({doi})' for doi in set(query.doi)]

        if len(parts) == 0:
            raise ValueError('Found no scopus ids or DOIs to query scopus')

        advanced_query = ' OR '.join(parts)

        next_cursor = '*'
        n_pages = 0
        n_records = 0
        while True:
            logger.info(f'Fetching page {n_pages}...')
            key = cls.get_api_keys(db_engine=db_engine, auth_key=auth_key)[0]

            page = httpx.get(
                'https://api.elsevier.com/content/search/scopus',
                params={
                    'query': advanced_query,
                    'cursor': next_cursor,
                    'view': 'COMPLETE',
                },
                headers={
                    'Accept': 'application/json',
                    "X-ELS-APIKey": key.api_key,
                },
                proxy=key.proxy,
            )

            key.scopus_requests_limit = page.headers.get('x-ratelimit-limit')
            key.scopus_requests_remaining = page.headers.get('x-ratelimit-remaining')
            key.scopus_requests_reset = page.headers.get('x-ratelimit-reset')
            cls.log_api_key_use(db_engine=db_engine, key=key)

            n_pages += 1
            data = page.json()

            next_cursor = get(data, 'search-results', 'cursor', '@next', default=None)
            entries = get(data, 'search-results', 'entry', default=[])

            if len(entries) == 0:
                break

            for entry in entries:
                n_records += 1
                yield Record(
                    title=cls.get_title(entry),
                    abstract=cls.get_abstract(entry),
                    doi=cls.get_doi(entry),
                    scopus_id=cls.get_id(entry),
                    raw_scopus=entry,
                    time_scopus=datetime.now(),
                    requested_scopus=True,
                )
            logger.debug(f'Found {n_records:,} records after processing page {n_pages}')
