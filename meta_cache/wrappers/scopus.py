import logging
from datetime import datetime
from typing import Any, Generator

import httpx
from sqlalchemy import select, desc
from sqlmodel import Session

from meta_cache.data import DatabaseEngine
from meta_cache.data.crud import Query

from meta_cache.data.schema import ApiKey, Record
from meta_cache.wrappers.base import AbstractWrapper, Request, get

logger = logging.getLogger('wrapper-scopus')
PAGE_SIZE = 25


class ScopusWrapper(AbstractWrapper):

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
    def get_api_key(session: Session) -> ApiKey:
        stmt = (
            select(ApiKey)
            .where(ApiKey.active)
            .order_by(desc(ApiKey.requests_remaining))
            .limit(1)
        )
        key = session.exec(stmt).one_or_none()
        if key is None:
            raise PermissionError('No valid Scopus API key left!')
        return key

    @classmethod
    def fetch(cls, db_engine: DatabaseEngine, query: Query) -> Generator[Record, None, None]:
        parts = []
        scopus_ids = set()
        if query.scopus_id:
            parts += [f'EID({sid})' for sid in query.scopus_id]
            scopus_ids = set(query.scopus_id)

        dois = set()
        if query.doi:
            parts += [f'DOI({doi})' for doi in query.doi]
            dois = set(query.doi)

        if len(parts) == 0:
            raise ValueError('Found no scopus ids or DOIs to query scopus')

        advanced_query = ' OR '.join(parts)

        next_cursor = '*'
        n_pages = 0
        n_records = 0
        with db_engine.session() as session:
            while True:
                logger.info(f'Fetching page {n_pages}...')
                key = cls.get_api_key(session=session)
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
                )

                key.requests_limit = page.headers.get('x-ratelimit-limit')
                key.requests_remaining = page.headers.get('x-ratelimit-remaining')
                key.requests_reset = page.headers.get('x-ratelimit-reset')
                session.commit()

                n_pages += 1
                data = page.json()

                next_cursor = get(data, 'search-results', 'cursor', '@next', default=None)
                entries = get(data, 'search-results', 'entry', default=[])

                if len(entries) == 0:
                    break

                for entry in entries:

                    doi = cls.get_doi(entry)
                    if doi is not None:
                        dois.remove(doi)

                    scopus_id = entry.get('eid')
                    if scopus_id is not None:
                        scopus_ids.remove(scopus_id)

                    n_records += 1
                    yield Record(
                        title=cls.get_title(entry),
                        abstract=cls.get_abstract(entry),
                        doi=doi,
                        scopus_id=scopus_id,
                        raw_scopus=entry,
                        time_scopus=datetime.now(),
                        requested_scopus=True,
                    )
                logger.debug(f'Found {n_records:,} records after processing page {n_pages}')

            logger.info(f'Number of missing DOIs: {len(dois)} | Number of missing scopus IDs: {len(scopus_ids)}')

            for doi in dois:
                yield Record(
                    doi=doi,
                    time_scopus=datetime.now(),
                    requested_scopus=False,
                )

            for scopus_id in scopus_ids:
                yield Record(
                    scopus_id=scopus_id,
                    time_scopus=datetime.now(),
                    requested_scopus=False,
                )
