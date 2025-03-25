import logging
from datetime import datetime
from typing import Any, Generator, Literal

import httpx

from meta_cache.handlers.db import DatabaseEngine
from meta_cache.handlers.models import Reference, Record
from meta_cache.handlers.util import get, RequestClient
from meta_cache.handlers.wrappers.base import AbstractWrapper
from meta_cache.handlers.schema import ApiKey

logger = logging.getLogger('wrapper-wos')
# Documentation:
# https://developer.clarivate.com/apis/wos-starter#
# https://api.clarivate.com/swagger-ui/?url=https%3A%2F%2Fdeveloper.clarivate.com%2Fapis%2Fwos-starter%2Fswagger
# https://github.com/clarivate/wosstarter_python_client/
PAGE_SIZE = 50  # 1-50

# WOS - Web of Science Core collection
# BIOABS - Biological Abstracts
# BCI - BIOSIS Citation Index
# BIOSIS - BIOSIS Previews
# CCC - Current Contents Connect
# DIIDW - Derwent Innovations Index
# DRCI - Data Citation Index
# MEDLINE - MEDLINE The U.S. National Library of Medicine® (NLM®) premier life sciences database.
# ZOOREC - Zoological Records
# PPRN - Preprint Citation Index
# WOK - All databases
Database = Literal['BCI', 'BIOABS', 'BIOSIS', 'CCC', 'DIIDW', 'DRCI', 'MEDLINE', 'PPRN', 'WOK', 'WOS', 'ZOOREC']


class WebOfScienceWrapper(AbstractWrapper):
    name = 'wos'
    db_field_id = 'wos_id'
    db_field_raw = 'raw_wos'
    db_field_time = 'time_wos'
    db_field_requested = 'requested_wos'

    @staticmethod
    def get_title(obj: dict[str, Any]) -> str | None:
        # FIXME
        return obj.get('dc:title')

    @staticmethod
    def get_abstract(obj: dict[str, Any]) -> str | None:
        # FIXME
        return obj.get('dc:description')

    @staticmethod
    def get_doi(obj: dict[str, Any]) -> str | None:
        # FIXME
        return obj.get('prism:doi')

    @staticmethod
    def get_id(obj: dict[str, Any]) -> str | None:
        # FIXME
        return obj.get('eid')

    @staticmethod
    def _api_key_query_extra() -> str:
        # FIXME
        return 'AND (api_key.scopus_requests_remaining IS NULL OR api_key.scopus_requests_remaining > 0)'

    @classmethod
    def log_api_key_use(cls, db_engine: DatabaseEngine, key: ApiKey) -> None:
        with db_engine.session() as session:
            orm_key = session.get(ApiKey, key.api_key_id)
            if not orm_key:
                logger.warning(f'Failed to log API key use: {key}')
            # FIXME
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

        DOIs = ' '.join([reference.doi for reference in references if reference.doi])
        PMIDs = ' '.join([reference.pubmed_id for reference in references if reference.pubmed_id])
        parts = []
        if len(DOIs)>0:
            parts.append(f'DOI=({DOIs})')
        if len(PMIDs)>0:
            parts.append(f'PMID=({PMIDs})')

        if len(parts) == 0:
            raise ValueError('Found no scopus ids or DOIs to query scopus')

        advanced_query = ' OR '.join(parts)

        next_cursor = '*'
        n_pages = 0
        n_records = 0
        n_results = 0
        while True:
            logger.info(f'Fetching page {n_pages}...')
            key = cls.get_api_keys(db_engine=db_engine, auth_key=auth_key)[0]

            page = httpx.get(
                'https://api.clarivate.com/apis/wos-starter/v1/documents',
                params={
                    'query': advanced_query,
                    'cursor': next_cursor,
                },
                headers={
                    'Accept': 'application/json',
                    "X-ApiKey": key.api_key,
                },
                proxy=key.proxy,
                timeout=120,
            )
            print(page)

            raise Exception()
            # res = httpx.get('https://api.clarivate.com/apis/wos-starter/v1/documents/',
            #                 params={'q': 'TS=(school uniform)', 'db': 'WOK', 'limit': 50, 'cursor': '*'},
            #                 headers={"X-ApiKey": 'xxx'}, timeout=120)

            # FIXME
            key.scopus_requests_limit = page.headers.get('x-ratelimit-limit')
            key.scopus_requests_remaining = page.headers.get('x-ratelimit-remaining')
            key.scopus_requests_reset = page.headers.get('x-ratelimit-reset')
            cls.log_api_key_use(db_engine=db_engine, key=key)

            n_pages += 1
            data = page.json()

            # FIXME
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
                    scopus_id=cls.get_id(entry),# FIXME
                    raw_scopus=entry,# FIXME
                    time_scopus=datetime.now(),# FIXME
                    requested_scopus=True,# FIXME
                )
            logger.debug(f'Found {n_records:,} records after processing page {n_pages}')


if __name__ == '__main__':
    from meta_cache.server.db import db_engine as engine
    import os

    for ri, record in enumerate(WebOfScienceWrapper.fetch(
            db_engine=engine,
            references=[Reference(doi='10.4103/ija.ija_382_20', openalex_id='W3095414299'),
                        Reference(doi='10.1111/jfr3.12673', openalex_id='W3095428461'),
                        Reference(doi='10.18517/ijaseit.10.5.10817', openalex_id='W3095407431'),
                        Reference(doi='10.1080/00141844.2020.1839527', openalex_id='W3095413630')],
            auth_key=os.getenv('AUTH_KEY'))):
        print(record)
        if ri > 100:
            break
    print('Force stopped')
