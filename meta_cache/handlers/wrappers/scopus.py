import logging
from datetime import datetime
from typing import Any, Generator

import httpx

from meta_cache.handlers.db import DatabaseEngine
from meta_cache.handlers.models import Reference, Record
from meta_cache.handlers.util import get, RequestClient
from .base import AbstractWrapper
from ..schema import ApiKey

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
    def log_api_key_use(cls, db_engine: DatabaseEngine, key: ApiKey) -> None:
        with db_engine.session() as session:
            orm_key = session.get(ApiKey, key.api_key_id)
            if not orm_key:
                logger.warning(f'Failed to log API key use: {key}')
            orm_key.sqlmodel_update({
                'scopus_requests_limit': key.scopus_requests_limit,
                'scopus_requests_remaining': key.scopus_requests_remaining,
                'scopus_requests_reset': key.scopus_requests_reset
            })
            session.add(orm_key)
            session.commit()

    @classmethod
    def fetch(cls,
              db_engine: DatabaseEngine,
              references: list[Reference],
              auth_key: str) -> Generator[Record, None, None]:
        parts = []
        for reference in references:
            if reference.scopus_id:
                parts.append(f'EID({reference.scopus_id})')
            if reference.doi:
                parts.append(f'DOI({reference.doi})')

        if len(parts) == 0:
            raise ValueError('Found no scopus ids or DOIs to query scopus')

        advanced_query = ' OR '.join(parts)

        with RequestClient() as request_client: # FIXME use AsyncRequestClient
            next_cursor = '*'
            n_pages = 0
            n_records = 0
            while True:
                logger.info(f'Fetching page {n_pages}...')
                key = cls.get_api_keys(db_engine=db_engine, auth_key=auth_key)[0]
                request_client.switch_proxy(proxy=key.proxy)

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
                n_results = get(data, 'search-results', 'opensearch:totalResults', default=0)

                if len(entries) == 0 or n_results == 0:
                    break
                if len(entries) == 1 and entries[0].get('error') is not None:
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

            # return {
            #     'n_records': n_records,
            #     'n_pages': n_pages,
            #     'n_results': n_results,
            # }
