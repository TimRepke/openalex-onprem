import orjson as json
import logging
from datetime import datetime
from typing import Annotated, Generator, Iterator
from itertools import batched

import httpx
import typer
from nacsos_data.models.openalex import WorksSchema
from nacsos_data.util.academic.apis.openalex import translate_work_to_solr

from nacsos_data.util.conf import OpenAlexConfig
from nacsos_data.util.academic.apis import OpenAlexSolrAPI

from .util import it_limit
from .schema import Request

logger = logging.getLogger('openalex.shared.solr')


def get_entries_with_missing_abstracts(
    config: OpenAlexConfig,
    openalex_ids: list[str] | None = None,
    created_since: Annotated[datetime | None, typer.Option(help='Get works created on or after')] = None,
    created_until: Annotated[datetime | None, typer.Option(help='Get works created on or after')] = None,
    limit: int = 1000,
) -> Generator[tuple[str, str, str], None, None]:
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
        created_since_ = created_since.strftime('%Y-%m-%dT23:58:58Z')
        created_until_ = (created_since or datetime.now()).strftime('%Y-%m-%dT00:00:00Z')
        logger.debug(f'Asking solr for records with missing abstracts from {created_since_} TO {created_until_}.')

        it = client.fetch_raw(
            query=f"""
            -abstract:*
            AND (
                 created_date:[{created_since_} TO {created_until_}]
              OR updated_date:[{created_since_} TO {created_until_}]
            )""",
            params={
                'fl': 'id,doi,id_pmid',
                'q.op': 'AND',
                'useParams': '',
                'defType': 'lucene',
            },
        )
        logger.info(f'Requested records with missing abstract from {created_since} TO {created_until}; Found {client.num_found:,} and limiting to {limit:,}.')
    else:
        raise AttributeError('At least one of `openalex_ids` or `created_since` must be specified!')

    yield from ((record['id'], record['doi'], record['id_pmid']) for record in it_limit(it, limit=limit))

    logger.info('Finished iterating records with missing abstracts.')


def write_cache_records_to_solr(
    config: OpenAlexConfig,
    records: list[Request],
    force: bool = False,
    batch_size: int = 200,
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

        buffer = b''
        timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        for record in batch_records:
            if needs_update is not None and record.openalex_id not in needs_update:
                continue

            rec = {
                'id': record.openalex_id,
                'title': {'set': record.title},
                'abstract': {'set': record.abstract},
                'title_abstract': {'set': f'{record.title} {record.abstract}'},
                'abstract_source': {'set': record.wrapper},
                'abstract_date': {'set': timestamp},
            }
            buffer += json.dumps(rec) + b'\n'

        res = httpx.post(
            f'{config.solr_url}/update/json?commit=true',
            headers={'Content-Type': 'application/json'},
            content=buffer.decode(),
            timeout=120,
        )

        logger.info(f'Partition posted to solr via {res}')

    return n_total, n_skipped


def write_api_update_to_solr(
    config: OpenAlexConfig,
    works: Iterator[WorksSchema],
) -> None:
    """Submit new or updated records to solr.
    This makes sure that we don't accidentally delete abstracts along the way.
    This always replaces all fields with the new value for exising IDs, except for the abstract field.

    1) Request entries from solr with the OpenAlex IDs of the records (works) to submit
    2) For works without prior record in solr -> submit as is
    3) For works we already have in solr
        * if existing record has no abstract -> write full update to solr
        * if existing record has abstract and work has abstract -> write full update to solr (if necessary, set the appropriate `abstract_source`)
        * if existing record has abstract and work has no abstract -> keep old abstract and set `abstract_source` to 'OpenAlex_old'
        * if abstract changed in any way, set the `abstract_date`
    """
    res: httpx.Response | None = None
    try:
        solr_works = {w.id: translate_work_to_solr(w, source=w.abstract_source or 'OpenAlex', authorship_limit=50) for w in works}
        res = httpx.post(
            f'{config.solr_url}/select',
            data={
                'fq': ['abstract:*', f'id:({" OR ".join(solr_works.keys())})'],
                'fl': 'id,abstract_source',
                'rows': len(solr_works),
            },
            timeout=60,
        )
        existing_works = res.json()['response']['docs']
        logger.debug(f'Checked {len(solr_works)} OpenAlex IDs and found {len(existing_works)} with an abstract in solr.')

        timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        for exising_work in existing_works:
            if exising_work['id'] not in solr_works:
                continue
            new_work = solr_works[exising_work['id']]
            if new_work['abstract'] is None and exising_work['abstract'] is not None:
                # update abstract source to indicate it's deprecated in OpenAlex or keep the previous non-OpenAlex source
                solr_works[exising_work['id']]['abstract_source'] = (
                    'OpenAlex_old' if exising_work['abstract_source'] == 'OpenAlex' else exising_work['abstract_source']
                )

            if new_work['abstract'] != exising_work['abstract']:
                solr_works[exising_work['id']]['abstract_date'] = timestamp

        res = httpx.post(
            url=f'{config.solr_collections_url}/update/json?commit=true',
            timeout=240,
            headers={'Content-Type': 'application/json'},
            content=b'\n'.join([json.dumps(w) for w in solr_works.values()]).decode(),
        )
        res.raise_for_status()
    except httpx.HTTPError as e:
        if res:
            logger.error(res.text)
        logger.error(f'Failed to submit: {e}')
        logger.exception(e)
