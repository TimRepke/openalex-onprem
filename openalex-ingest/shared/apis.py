import logging
import uuid
from typing import Generator
from datetime import datetime

import pandas as pd
from sqlalchemy import text
from nacsos_data.util.academic.apis import APIMap, AbstractAPI, APIEnum
from nacsos_data.util.academic.apis.dimensions import FIELDS as DIMENSIONS_FIELDS

from shared.db import DatabaseEngine
from shared.schema import ApiKey, Request, Queue, QueueRequests

ID_KEYS = ['doi', 'openalex_id', 'nacsos_id', 'pubmed_id', 's2_id', 'scopus_id', 'wos_id', 'dimensions_id', 'queue_id']


def get_reference_df(queries: list[Queue]) -> pd.DataFrame:
    return pd.DataFrame(
        [{k: getattr(ref, k) for k in ID_KEYS} for ref in queries],
    )


def complete_ids(req: Request, df_queue: pd.DataFrame) -> Request:
    for fld in ID_KEYS:
        val = getattr(req, fld)
        if val is None:
            continue
        for _, ref in df_queue[df_queue[fld] == val].iterrows():
            for ref_field in ID_KEYS:
                if ref[ref_field] is not None and getattr(req, ref_field) is None:
                    setattr(req, ref_field, ref[ref_field])
    return req


def pluck_ids(queries: list[Queue], *keys: str) -> dict[str, set[str]]:
    ids: dict[str, set[str]] = {key: set() for key in keys}
    for query in queries:
        for key in keys:
            if getattr(query, key) is not None:
                ids[key].add(getattr(query, key))
    return ids


def queries_to_scopus_str(queries: list[Queue]) -> str:
    parts = set()
    for reference in queries:
        if reference.scopus_id:
            parts.add(f'EID({reference.scopus_id})')
        if reference.doi:
            parts.add(f'DOI({reference.doi})')

    if len(parts) == 0:
        raise ValueError('Found no scopus ids or DOIs to query scopus')

    return ' OR '.join(parts)


def queries_to_wos_str(queries: list[Queue]) -> str:
    wosids: set[str] = {query.wos_id for query in queries if query.wos_id}
    dois: set[str] = {query.doi for query in queries if query.doi}
    pmids: set[str] = {query.pubmed_id for query in queries if query.pubmed_id}
    parts: list[str] = []
    if len(dois) > 0:
        parts.append(f'DO=({" ".join(dois)})')
    if len(pmids) > 0:
        parts.append(f'PMID=({" ".join(pmids)})')
    if len(wosids) > 0:
        parts.append(f'UT=({" ".join(wosids)})')

    if len(parts) == 0:
        raise ValueError('Found no pubmed ids, wos ids, or DOIs to query the web of science')

    return ' OR '.join(parts)


def queries_to_dimensions_str(queries: list[Queue]) -> str:
    ids = pluck_ids(queries, 'dimensions_id', 'doi', 'pubmed_id')
    where = []
    if len(ids.get('doi', [])) > 0:
        dois = [f'"{doi}"' for doi in ids['doi']]
        where.append(f'doi in [{",".join(dois)}]')
    if len(ids.get('dimensions_id', [])) > 0:
        dids = [f'"{did}"' for did in ids['dimensions_id']]
        where.append(f'id in [{",".join(dids)}]')
    if len(ids.get('dimensions_id', [])) > 0:
        pmids = [f'"{pmid}"' for pmid in ids['pubmed_id']]
        where.append(f'pmid in [{",".join(pmids)}]')

    if len(where) == 0:
        raise ValueError('Found no pmids, dimensions ids or DOIs to query dimensions')

    return f'search publications where {" or ".join(where)} return publications[{"+".join(DIMENSIONS_FIELDS)}]'


def queries_to_pubmed_str(queries: list[Queue]) -> str:
    parts = set()
    for query in queries:
        if query.pubmed_id:
            parts.add(f'{query.pubmed_id}[PMID]')
        if query.doi:
            parts.add(f'{query.doi}[DOI]')

    if len(parts) == 0:
        raise ValueError('Found no pubmed ids or DOIs to query pubmed')
    return ' OR '.join(parts)


class APIWrapper:
    def __init__(self, wrapper: str, db_engine: DatabaseEngine, auth_key: str, logger: logging.Logger | None = None):
        if wrapper not in APIMap:
            raise AttributeError(f'API key {wrapper} is not a known API wrapper')
        self.wrapper = wrapper
        self.db_engine = db_engine
        self.auth_key = auth_key
        self.logger = logger or logging.getLogger('api-wrapper')

    def fetch(self, queries: list[Queue | QueueRequests]) -> Generator[Request, None, None]:
        """
        1) pick an available key
        2) determine which API to use
        3) fetch max per request
        4) update key usage (via api_feedback)
        5) for each result
            ~ api.translate -> title, abstract, doi, IDs, wrapper, ...
            ~ merge result with requested IDs
            ~ yield result as Request
        """
        if len(queries) == 0:
            raise StopIteration()

        extra_params = {}
        if self.wrapper == APIEnum.DIMENSIONS.value:
            extra_params = {'override_content': True}

        key = self._get_api_key()
        api: AbstractAPI = APIMap[self.wrapper](api_key=key.api_key, proxy=key.proxy, logger=self.logger.getChild('api'), **extra_params)

        if len(queries) > api.PAGE_MAX:
            self.logger.warning(f'Going to ignore some queries because you requested too many at once! Maximum is {api.PAGE_MAX}')

        results_raw = list(api.fetch_raw(query=self._queries_to_query_str(queries)))
        results_trans = [api.translate_record(record) for record in results_raw]

        key.api_feedback = api.api_feedback
        self._log_api_key_use(key)

        requests = (
            Request(
                record_id=uuid.uuid4(),
                wrapper=self.wrapper,
                api_key_id=key.api_key_id,
                openalex_id=res_t.openalex_id,
                nacsos_id=None,  # explicit none because we never query nacsos for this
                doi=res_t.doi,
                s2_id=res_t.s2_id,
                scopus_id=res_t.scopus_id,
                wos_id=res_t.wos_id,
                dimensions_id=res_t.dimensions_id,
                pubmed_id=res_t.pubmed_id,
                title=res_t.title,
                abstract=res_t.text,
                time_created=datetime.now(),
                raw=res_r,
            )
            for res_t, res_r in zip(results_trans, results_raw, strict=False)
        )

        df_ids = get_reference_df(queries)
        yield from (complete_ids(req, df_ids) for req in requests)

    def _queries_to_query_str(self, queries: list[Queue]) -> str:
        if self.wrapper == 'SCOPUS':
            return queries_to_scopus_str(queries)
        if self.wrapper == 'WOS':
            return queries_to_wos_str(queries)
        if self.wrapper == 'DIMENSIONS':
            return queries_to_dimensions_str(queries)
        if self.wrapper == 'PUBMED':
            return queries_to_pubmed_str(queries)
        raise NotImplementedError(f'API wrapper {self.wrapper} not implemented')

    def _log_api_key_use(self, key: ApiKey) -> None:
        with self.db_engine.session() as session:
            orm_key = session.get(ApiKey, key.api_key_id)
            if not orm_key:
                self.logger.warning(f'Failed to log API key use: {key}')
                return

            orm_key.sqlmodel_update(
                {
                    'api_feedback': key.api_feedback,
                    'last_used': datetime.now(),
                },
            )
            session.add(orm_key)
            session.commit()

    def _get_api_key(self) -> ApiKey:
        with self.db_engine.session() as session:
            keys = session.exec(
                text(
                    """
                    SELECT api_key.*
                    FROM api_key
                         JOIN m2m_auth_api_key ON api_key.api_key_id = m2m_auth_api_key.api_key_id
                         JOIN auth_key ON m2m_auth_api_key.auth_key_id = auth_key.auth_key_id
                    WHERE auth_key.auth_key_id = :auth_key
                      AND auth_key.active IS TRUE
                      AND api_key.active IS TRUE
                      AND api_key.wrapper = :wrapper
                    ORDER BY last_used
                    LIMIT 1;""",
                ),
                params={
                    'wrapper': self.wrapper,
                    'auth_key': self.auth_key,
                },
            ).all()
            if keys is None or len(keys) == 0:
                raise PermissionError(f'No valid {self.wrapper} API key available for this user!')
            return [ApiKey.model_validate(key) for key in keys][0]
