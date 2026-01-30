import json
import logging
from typing import Annotated, Generator, Iterator
from itertools import batched

import httpx
import typer

from nacsos_data.util.conf import OpenAlexConfig
from nacsos_data.util.academic.apis import OpenAlexSolrAPI

from .util import date_check, it_limit
from .schema import Request

logger = logging.getLogger('openalex.shared.solr')


def get_entries_with_missing_abstracts(
    config: OpenAlexConfig,
    openalex_ids: list[str] | None = None,
    created_since: Annotated[str | None, typer.Option(callback=date_check, help='Get works created on or after')] = None,
    created_until: Annotated[
        str | None,
        typer.Option(
            callback=date_check,
            help='Get works created on or after',
        ),
    ] = None,
    limit: int = 1000,
) -> Generator[tuple[str, str], None, None]:
    if created_until is None:
        created_until = 'NOW'
    else:
        created_until = f'{created_since}T00:00:00Z'

    client = OpenAlexSolrAPI(openalex_conf=config)
    if openalex_ids is not None and len(openalex_ids) > 0:
        logger.debug('Asking solr for which IDs are missing abstracts.')
        it = client.fetch_raw(
            query='-abstract:*',  # -abstract:[* TO ""],
            params={
                'fq': f'id:({" OR ".join(openalex_ids)})',
                'fl': 'id,doi',
                'q.op': 'AND',
                'useParams': '',
                'defType': 'lucene',
            },
        )
        logger.info(f'Requested {len(openalex_ids):,} of which {client.num_found:,} (will limit to {limit:,}) have no abstract in solr.')
    elif created_since is not None:
        logger.debug(f'Asking solr for records with missing abstracts from {created_since} TO {created_until}.')
        it = client.fetch_raw(
            query='-abstract:*',
            params={
                'fq': f'created_date:[{created_since}T00:00:00Z TO {created_until}]',
                'fl': 'id,doi',
                'q.op': 'AND',
                'useParams': '',
                'defType': 'lucene',
            },
        )
        logger.info(f'Requested records with missing abstract from {created_since} TO {created_until}; Found {client.num_found:,} and limiting to {limit:,}.')
    else:
        raise AttributeError('At least one of `openalex_ids` or `created_since` must be specified!')

    yield from ((record['id'], record['doi']) for record in it_limit(it, limit=limit))

    logger.info('Finished iterating records with missing abstracts.')


def write_cache_records_to_solr(
    config: OpenAlexConfig,
    records: Iterator[Request],
    force: bool = False,
    batch_size: int = 100,
) -> tuple[int, int]:
    n_total = 0
    n_skipped = 0
    for batch in batched(records, batch_size, strict=False):
        batch_records = list(batch)
        n_total += len(batch_records)
        needs_update: set[str] | None = None
        if not force:
            openalex_ids = [record.openalex_id for record in records]
            needs_update = {oa_id for oa_id, _ in get_entries_with_missing_abstracts(config=config, openalex_ids=openalex_ids)}
            n_skipped += len(batch_records) - len(needs_update)
            if len(needs_update) <= 0:
                logger.info('Partition skipped, seems complete')
                continue

        buffer = ''
        for record in batch_records:
            if needs_update is not None and record.openalex_id not in needs_update:
                continue

            rec = {
                'id': record.openalex_id,
                'title': {'set': record.title},
                'abstract': {'set': record.abstract},
                'title_abstract': {'set': f'{record.title} {record.abstract}'},
                'abstract_source': record.wrapper,
            }
            if record.doi:
                rec['doi'] = f'https://doi.org/{record.doi}'
            buffer += json.dumps(rec) + '\n'

        res = httpx.post(
            f'{config.solr_url}/update/json?commit=true',
            headers={'Content-Type': 'application/json'},
            data=buffer,
            timeout=120,
        )

        logger.info(f'Partition posted to solr via {res}')

    return n_total, n_skipped
