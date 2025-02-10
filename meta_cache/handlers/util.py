import asyncio
import json
import logging
import typing
from datetime import datetime
from time import perf_counter, sleep
from typing import Any

import httpx
import pandas as pd
from httpx import Client, URL, USE_CLIENT_DEFAULT, Response, AsyncClient, codes
from httpx._client import UseClientDefault
from httpx._types import RequestContent, RequestData, RequestFiles, QueryParamTypes, HeaderTypes, CookieTypes, \
    AuthTypes, TimeoutTypes, RequestExtensions
from sqlalchemy import select
from sqlalchemy.sql._typing import _ColumnExpressionArgument
from typing_extensions import override

from .db import DatabaseEngine
from .models import Reference
from .schema import Record

logger = logging.getLogger('util')


def get(obj: dict[str, Any], *keys, default: Any = None) -> Any | None:
    for key in keys:
        obj = obj.get(key)
        if obj is None:
            return default
    return obj


def get_reference_df(references: list[Reference]) -> pd.DataFrame:
    df = pd.DataFrame([ref.model_dump() for ref in references])

    # Extra fields for status tracking
    df['hit'] = None
    df['queued'] = None
    df['updated'] = None
    df['added'] = None
    # Set all as missed by default
    df['missed'] = True

    # Extra fields for cache hits
    df['record_id'] = None
    df['title'] = None
    df['abstract'] = None

    # Ensure all reference fields are there
    for field in (set(Reference.keys()) - set(df.columns)):
        df[field] = None

    return df


def mark_status(df: pd.DataFrame, record: Record, status: str = 'hit'):
    for field, value in Reference.ids(record):
        mask = df[field] == value
        df.loc[mask, 'missed'] = False
        df.loc[mask, status] = True
        if record.record_id:
            df.loc[mask, 'record_id'] = record.record_id
        if record.title:
            df.loc[mask, 'title'] = record.title
        if record.abstract:
            df.loc[mask, 'abstract'] = record.abstract


def get_ors(reference: Reference | Record) -> list[_ColumnExpressionArgument[bool]]:
    return [
        getattr(Record, field) == value
        for field, value in Reference.ids(reference)
    ]


def post2solr(records: list[Record], solr_host: str, collection: str, force: bool = False) -> tuple[int, int]:
    needs_update: set[str] | None = None
    if not force:
        logging.debug(f'Asking solr for which IDs are missing abstracts...')
        res = httpx.get(f'{solr_host}/api/collections/{collection}/select',
                        params={
                            'q': '-abstract:*',  # -abstract:[* TO ""]
                            'fq': f'id:({' OR '.join([record.openalex_id for record in records])})',
                            'fl': 'id',
                            'q.op': 'AND',
                            'rows': len(records),
                            'useParams': '',
                            'defType': 'lucene'
                        }).json()

        needs_update = set([doc['id'] for doc in res['response']['docs']])
        logger.info(f'Partition with {len(records):,} records '
                    f'has {len(needs_update):,} missing abstracts in solr')

        if len(needs_update) <= 0:
            logger.info(f'Partition skipped, seems complete')
            return 0, len(records)

    buffer = ''
    for record in records:
        if needs_update is not None and record.openalex_id not in needs_update:
            continue

        rec = {
            'id': record.openalex_id,
            'title': record.title,
            'abstract': record.abstract,
            'title_abstract': f'{record.title} {record.abstract}',
            'external_abstract': True,
        }
        if record.doi:
            rec['doi'] = f'https://https://doi.org/{record.doi}'
        buffer += json.dumps(rec) + '\n'

    res = httpx.post((f'{solr_host}/api/collections/{collection}/update/json?commit=true'),
                     headers={'Content-Type': 'application/json'},
                     data=buffer)

    logger.info(f'Partition posted to solr via {res}')

    return len(needs_update), len(records) - len(needs_update)


def update_solr_abstracts(db_engine: DatabaseEngine,
                          solr_host: str,
                          solr_collection: str,
                          batch_size: int = 200,
                          from_time: datetime | None = None,
                          force_override: bool = False):
    with db_engine.engine.connect() as connection:
        stmt = select(Record).where(Record.openalex_id != None,
                                    Record.abstract != None,
                                    Record.title != None)
        if from_time is not None:
            stmt = stmt.where(Record.time_updated >= from_time)

        with connection.execution_options(yield_per=batch_size).execute(stmt) as result:
            for pi, partition in enumerate(result.partitions(batch_size)):
                logger.debug(f'Received partition {pi} from meta-cache.')
                n_updated, n_skipped = post2solr(records=list(partition),
                                                 solr_host=solr_host,
                                                 collection=solr_collection,
                                                 force=force_override)
                logger.debug(f'Updated {n_updated} and skipped {n_skipped} records.')


class AsyncRequestClient(AsyncClient):
    def __init__(self, *,
                 max_req_per_sec: int = 5, max_retries: int = 5, timeout_rate: float = 5.,
                 retry_on_status: list[int] | None = None,
                 **kwargs):
        super().__init__(**kwargs)

        self.max_req_per_sec = max_req_per_sec
        self.time_per_request = 1 / max_req_per_sec
        self.max_retries = max_retries
        self.timeout_rate = timeout_rate
        self.last_request: float | None = None
        self.retry_on_status = retry_on_status or [
            codes.INTERNAL_SERVER_ERROR,  # 500
            codes.BAD_GATEWAY,  # 502
            codes.SERVICE_UNAVAILABLE,  # 503
            codes.GATEWAY_TIMEOUT,  # 504
        ]

    @override
    async def request(
            self,
            method: str,
            url: URL | str,
            *,
            content: RequestContent | None = None,
            data: RequestData | None = None,
            files: RequestFiles | None = None,
            json: typing.Any | None = None,
            params: QueryParamTypes | None = None,
            headers: HeaderTypes | None = None,
            cookies: CookieTypes | None = None,
            auth: AuthTypes | UseClientDefault | None = USE_CLIENT_DEFAULT,
            follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
            timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
            extensions: RequestExtensions | None = None,
    ) -> Response:
        for _ in range(self.max_retries):
            # Check if we need to wait before the next request so we are staying below the rate limit
            time = perf_counter() - (self.last_request or 0)
            if time < self.time_per_request:
                logging.debug(f'Sleeping to keep rate limit: {self.time_per_request - time:.4f} seconds')
                await asyncio.sleep(self.time_per_request - time)

            # Log latest request
            self.last_request = perf_counter()

            response = await super().request(method=method, url=url, content=content, data=data, files=files, json=json,
                                             params=params, headers=headers, cookies=cookies, auth=auth,
                                             follow_redirects=follow_redirects, timeout=timeout, extensions=extensions)

            try:
                response.raise_for_status()

                # reset counters after successful request
                self.time_per_request = 1 / self.max_req_per_sec

                return response

            except httpx.HTTPError as e:
                # if this error is not on the list, pass on error right away; otherwise log and retry
                if e.response.status_code not in self.retry_on_status and len(self.retry_on_status) > 0:
                    raise e

                logging.error(f'Failed to submit {url}: {e}')
                logging.warning(e.response.text)
                logging.exception(e)

                # grow the sleep time between requests
                self.time_per_request = (self.time_per_request + 1) * self.timeout_rate
        else:
            raise RuntimeError('Maximum number of retries reached')


class RequestClient(Client):
    # FIXME is there a more graceful way to have (the logic for) sync and async versions in one class?
    def __init__(self, *,
                 max_req_per_sec: int = 5, max_retries: int = 5, timeout_rate: float = 5.,
                 retry_on_status: list[int] | None = None,
                 **kwargs):
        super().__init__(**kwargs)

        self.max_req_per_sec = max_req_per_sec
        self.time_per_request = 1 / max_req_per_sec
        self.max_retries = max_retries
        self.timeout_rate = timeout_rate
        self.last_request: float | None = None
        self.retry_on_status = retry_on_status or [
            codes.INTERNAL_SERVER_ERROR,  # 500
            codes.BAD_GATEWAY,  # 502
            codes.SERVICE_UNAVAILABLE,  # 503
            codes.GATEWAY_TIMEOUT,  # 504
        ]
        self.kwargs = kwargs
        self.callbacks = {}

    def switch_proxy(self, proxy: str | None = None):
        if proxy != self.kwargs.get('proxy'):
            client = self.__init__(**self.kwargs, proxy=proxy, max_req_per_sec=self.max_req_per_sec,
                                   max_retries=self.max_retries, timeout_rate=self.timeout_rate,
                                   retry_on_status=self.retry_on_status)
            self.__dict__.update(client.__dict__)

    def on(self, status: int, func: typing.Callable[[Response], dict[str, Any]]):
        self.callbacks[status] = func

    @override
    def request(
            self,
            method: str,
            url: URL | str,
            *,
            content: RequestContent | None = None,
            data: RequestData | None = None,
            files: RequestFiles | None = None,
            json: typing.Any | None = None,
            params: QueryParamTypes | None = None,
            headers: HeaderTypes | None = None,
            cookies: CookieTypes | None = None,
            auth: AuthTypes | UseClientDefault | None = USE_CLIENT_DEFAULT,
            follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
            timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
            extensions: RequestExtensions | None = None,
    ) -> Response:
        for retry in range(self.max_retries):
            # Check if we need to wait before the next request so we are staying below the rate limit
            time = perf_counter() - (self.last_request or 0)
            if time < self.time_per_request:
                logging.debug(f'Sleeping to keep rate limit: {self.time_per_request - time:.4f} seconds')
                sleep(self.time_per_request - time)

            # Log latest request
            self.last_request = perf_counter()

            response = super().request(method=method, url=url, content=content, data=data, files=files, json=json,
                                       params=params, headers=headers, cookies=cookies, auth=auth,
                                       follow_redirects=follow_redirects, timeout=timeout, extensions=extensions)

            try:
                response.raise_for_status()

                # reset counters after successful request
                self.time_per_request = 1 / self.max_req_per_sec

                return response

            except httpx.HTTPError as e:
                if e.response.status_code in self.callbacks:
                    logger.debug(f'Found status handler for {e.response.status_code}')
                    update = self.callbacks[e.response.status_code](e.response)
                    if update and update.get('content'):
                        content = update.get('content')
                    if update and update.get('data'):
                        data = update.get('data')
                    if update and update.get('json'):
                        json.update(update.get('json', {}))
                    if update and update.get('params'):
                        params.update(update.get('params', {}))
                    if update and update.get('headers'):
                        headers.update(update.get('headers', {}))

                # if this error is not on the list, pass on error right away; otherwise log and retry
                elif e.response.status_code not in self.retry_on_status and len(self.retry_on_status) > 0:
                    raise e

                else:
                    logging.warning(f'Retry {retry} after failing to retrieve from {url}: {e}')
                    logging.warning(e.response.text)
                    logging.exception(e)

                    # grow the sleep time between requests
                    self.time_per_request = (self.time_per_request + 1) * self.timeout_rate
        else:
            raise RuntimeError('Maximum number of retries reached')
