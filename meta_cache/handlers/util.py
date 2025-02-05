import json
import logging
from datetime import datetime
from typing import Any

import httpx
import pandas as pd
from sqlalchemy import select
from sqlalchemy.sql._typing import _ColumnExpressionArgument

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
