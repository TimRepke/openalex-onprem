import logging
import sys
from datetime import datetime
from typing import Any, Generator

import httpx
from httpx import HTTPError

from meta_cache.handlers.db import DatabaseEngine
from meta_cache.handlers.models import Reference, Record
from meta_cache.handlers.util import get, RequestClient
from meta_cache.handlers.wrappers.base import AbstractWrapper
from meta_cache.handlers.schema import ApiKey

# documentation:
# https://docs.dimensions.ai/dsl/language.html
# https://github.com/digital-science/dimcli/blob/master/dimcli/core/api.py

logger = logging.getLogger('wrapper-dimensions')
PAGE_SIZE = 1000


class DimensionsWrapper(AbstractWrapper):
    name = 'dimensions'
    db_field_id = 'dimensions_id'
    db_field_raw = 'raw_dimensions'
    db_field_time = 'time_dimensions'
    db_field_requested = 'requested_dimensions'

    FIELDS = [
        'title', 'type', 'abstract', 'authors_count', 'date',
        'year', 'authors', 'journal',  # 'journal.title',
        'document_type', 'doi', 'id',
        # 'linkout',
        'publisher',
        'research_org_country_names', 'research_org_names',
        'researchers', 'times_cited',
        'editors', 'supporting_grant_ids', 'book_doi', 'book_title', 'subtitles',
        'book_series_title', 'proceedings_title']

    @staticmethod
    def get_title(obj: dict[str, Any]) -> str | None:
        return obj.get('title')

    @staticmethod
    def get_abstract(obj: dict[str, Any]) -> str | None:
        return obj.get('abstract')

    @staticmethod
    def get_doi(obj: dict[str, Any]) -> str | None:
        return obj.get('doi')

    @staticmethod
    def get_id(obj: dict[str, Any]) -> str | None:
        return obj.get('id')

    @staticmethod
    def _api_key_query_extra() -> str:
        return ''

    @classmethod
    def log_api_key_use(cls, db_engine: DatabaseEngine, key: ApiKey) -> None:
        with db_engine.session() as session:
            orm_key = session.get(ApiKey, key.api_key_id)
            if not orm_key:
                logger.warning(f'Failed to log API key use: {key}')
            orm_key.sqlmodel_update({
                'dimensions_jwt': key.dimensions_jwt,
                'last_used': datetime.now(),
            })
            session.add(orm_key)
            session.commit()

    @classmethod
    def request(cls, body: str, db_engine: DatabaseEngine, auth_key: str):
        key = cls.get_api_keys(db_engine=db_engine, auth_key=auth_key)[0]
        with RequestClient(proxy=key.proxy, timeout=60) as request_client:  # FIXME use AsyncRequestClient

            def update_jwt(response: httpx.Response) -> dict[str, dict[str, str]]:
                logger.debug('Fetching JWT token')
                res = request_client.post('https://app.dimensions.ai/api/auth.json', json={'key': key.api_key})
                res.raise_for_status()
                key.dimensions_jwt = res.json()['token']
                return {'headers': {'Authorization': f'JWT {key.dimensions_jwt}'}}

            request_client.on(httpx.codes.UNAUTHORIZED, update_jwt)

            n_pages = 0
            n_records = 0
            while True:
                logger.info(f'Fetching page {n_pages}...')
                try:
                    page = request_client.post(
                        url='https://app.dimensions.ai/api/dsl/v2',
                        content=f'{body} limit {PAGE_SIZE} skip {n_pages * PAGE_SIZE}',
                        headers={
                            'Accept': 'application/json',
                            'Authorization': f'JWT {key.dimensions_jwt}',
                        },
                    )

                    cls.log_api_key_use(db_engine=db_engine, key=key)

                    n_pages += 1
                    data = page.json()

                    n_results = get(data, '_stats', 'total_count', default=0)
                    entries = get(data, 'publications', default=[])

                    if len(entries) == 0 or n_results == 0 or n_records >= n_results:
                        break

                    for entry in entries:
                        n_records += 1
                        yield Record(
                            title=cls.get_title(entry),
                            abstract=cls.get_abstract(entry),
                            doi=cls.get_doi(entry),
                            dimensions_id=cls.get_id(entry),
                            raw_dimensions=entry,
                            time_dimensions=datetime.now(),
                            requested_dimensions=True,
                        )
                    logger.debug(f'Found {n_records:,} records after processing page {n_pages} '
                                 f'(total {n_results:,} records)')
                except HTTPError as e:
                    logging.warning(f'Failed: {e}')
                    logging.warning(e.response.text)
                    logging.exception(e)
                    raise e

    @classmethod
    def fetch(cls,
              db_engine: DatabaseEngine,
              references: list[Reference],
              auth_key: str) -> Generator[Record, None, None]:
        parts = {'doi': [], 'id': []}
        for reference in references:
            if reference.dimensions_id:
                parts['id'].append(f'"{reference.dimensions_id}"')
            if reference.doi:
                parts['doi'].append(f'"{reference.doi}"')
        filters = [
            f'{key} in [{', '.join(ids)}]'
            for key, ids in parts.items()
            if len(ids) > 0
        ]

        if len(filters) == 0:
            raise ValueError('Found no dimensions ids or DOIs to query dimensions')

        where = ' OR '.join(filters)
        yield from cls.request(body=f'search publications '
                                    f'where {where} '
                                    f'return publications[{'+'.join(DimensionsWrapper.FIELDS)}]',
                               db_engine=db_engine,
                               auth_key=auth_key)


if __name__ == '__main__':
    from meta_cache.server.db import db_engine as engine
    import os

    # body = f'search publications where doi in [] return publications[{'+'.join(DimensionsWrapper.FIELDS)}]'
    # print(body)
    # for ri, record in enumerate(DimensionsWrapper.request(
    #         db_engine=engine,
    #         body=body,
    #         auth_key=os.getenv('AUTH_KEY'))):
    #     print(record)
    #     if ri > 100:
    #         break

    for ri, record in enumerate(DimensionsWrapper.fetch(
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
