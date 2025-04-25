import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer
import httpx

from meta_cache.handlers.db import get_engine
from meta_cache.handlers.models import Reference
from meta_cache.handlers.util import update_solr_abstracts
from meta_cache.handlers.wrappers import DimensionsWrapper, ScopusWrapper
from meta_cache.scripts.config import db_engine_cache
from shared.util import rate_limit, batched

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s (%(process)d): %(message)s', level='INFO')
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.WARNING)
logger = logging.getLogger('abstract-completion')
app = typer.Typer()


@app.command()
def openalex_ids(query: Annotated[str, typer.Option(help='query for openalex')],
                 file_ids: Path = Path('../../data/ids.txt'),
                 only_non_oa: bool = False,
                 use_stemming: bool = True,
                 search_fulltext: bool = False):
    if file_ids.exists():
        logger.warning('Data already exists, not downloading again')
        return

    cursor = '*'
    ids = 0
    page_i = 0

    fltr = []
    if only_non_oa:
        fltr.append('open_access.is_oa:false')
    if not search_fulltext:
        if use_stemming:
            fltr.append(f'title_and_abstract.search.no_stem: {query}')
        else:
            fltr.append(f'title_and_abstract.search: {query}')
    else:
        raise NotImplementedError()
    # published by springer or elsevier
    # f',primary_location.source.publisher_lineage:p4310320990|p4310319965'

    with open(file_ids, 'w') as f:
        while cursor is not None:
            page_i += 1
            with rate_limit(min_time_ms=100) as t:
                res = httpx.get(
                    'https://api.openalex.org/works',
                    params={
                        'filter': ','.join(fltr),
                        'select': 'id',
                        'cursor': cursor,
                        'per-page': 200
                    },
                    headers={'api_key': os.getenv('API_KEY')},
                    timeout=None,
                )
                page = res.json()
                cursor = page['meta']['next_cursor']
                logger.info(f'Retrieved {ids:,}/{page['meta']['count']:,}; currently on page {page_i}')

                page_ids = [raw_work['id'][21:] for raw_work in page['results']]
                ids += len(page_ids)
                f.write('\n'.join(page_ids) + '\n')


@app.command()
def request_ids(solr_host: Annotated[str, typer.Option(prompt='solr host')],
                solr_collection: Annotated[str, typer.Option(prompt='solr collection')],
                auth_key: Annotated[str, typer.Option(prompt='meta-cache key')],
                file_ids: Annotated[Path, typer.Option(prompt='path to file with ids to check')] = Path(
                    '../../data/ids.txt'),
                skip_until_id: str | None = None,
                skip_batches: int = 0,
                batch_size: int = 500):
    if not file_ids.exists():
        logger.error(f'Data does not exists: {file_ids}')
        return

    with open(file_ids) as f:
        oa_ids = list(set([oai_id.strip() for oai_id in f.readlines() if len(oai_id.strip()) > 0]))

    oa_ids = sorted(oa_ids)

    logger.info(f'Reading {len(oa_ids):,} from {file_ids}')

    if len(oa_ids) < 1:
        raise Exception(f'No OAI-IDs found in {file_ids}')

    found_starting_point = False

    with httpx.Client() as client:
        for bi, batch in enumerate(batched(oa_ids, batch_size)):
            logger.info(f'----------- Processing batch {bi} / {(len(oa_ids) // batch_size) + 1:,} -----------')
            if skip_batches > bi:
                logger.debug(f'Skipping batch {bi}')
                continue
            if skip_until_id and not found_starting_point:
                if skip_until_id not in batch:
                    logger.debug(f'Skipping batch {bi}')
                    continue
                found_starting_point = True

            res = client.get(f'{solr_host}/api/collections/{solr_collection}/select',
                             params={
                                 'q': '-abstract:*',  # -abstract:[* TO ""]
                                 'fq': f'id:({' OR '.join([bi.strip() for bi in batch])})',
                                 'fl': 'id,doi',
                                 'q.op': 'AND',
                                 'rows': batch_size,
                                 'useParams': '',
                                 'defType': 'lucene'
                             }).json()

            if len(res['response']['docs']) == 0:
                logger.debug('Batch has no missing abstracts in solr.')
                continue

            logger.info(f'Missing abstract for {len(res['response']['docs']):,} / {len(batch)} entries')

            references = [
                Reference(openalex_id=doc['id'], doi=doc['doi'][16:])
                for doc in res['response']['docs']
                if doc.get('doi') is not None
            ]
            if len(references) == 0:
                logger.debug('Batch has no DOIs.')
                continue
            logger.info(f'  > {len(references)} references with missing abstract have a DOI')

            # request dimensions
            cache_response = DimensionsWrapper.run(db_engine=db_engine_cache,
                                                   references=references,
                                                   auth_key=auth_key,
                                                   skip_existing=True)

            # with remaining request scopus
            remaining = [ref for ref in cache_response.references if ref.missed or not ref.abstract]
            if len(remaining) > 0:
                logger.info(f'{len(remaining):,} references remaining for scopus')
                cache_response = ScopusWrapper.run(db_engine=db_engine_cache,
                                                   references=[Reference(openalex_id=doc.openalex_id, doi=doc.doi)
                                                               for doc in remaining],
                                                   auth_key=auth_key,
                                                   skip_existing=True)

            # with remaining request wos
            remaining = [ref for ref in cache_response.references if ref.missed or not ref.abstract]
            if len(remaining) > 0:
                logger.info(f'{len(remaining):,} references remaining for the Web of Science')
                # TODO
                logger.warning('Not implemented, not investigating further...')

            # with remaining request s2
            # TODO


@app.command()
def push_cache(solr_host: Annotated[str, typer.Option(help='Solr base url')],
               solr_collection: Annotated[str, typer.Option(help='Name of the Solr collection')],
               conf_file: Annotated[str, typer.Option(help='Path to configuration .env file')],
               created_since: Annotated[str | None, typer.Option(help='Get works created on or after')] = None,
               batch_size: int = 200):
    logger.info(f'Connecting to database.')
    db_engine = get_engine(conf_file=conf_file)

    logger.info(f'Starting backfill of abstracts.')
    update_solr_abstracts(
        db_engine=db_engine,
        solr_host=solr_host,
        solr_collection=solr_collection,
        from_time=datetime.strptime(created_since, '%Y-%m-%d') if created_since is not None else None,
        batch_size=batch_size,
    )


@app.command()
def complete_abstracts(query: Annotated[str, typer.Option(help='query for openalex')],
                       solr_host: Annotated[str, typer.Option(help='Solr base url')],
                       solr_collection: Annotated[str, typer.Option(help='Name of the Solr collection')],
                       conf_file: Annotated[str, typer.Option(help='Path to configuration .env file')],
                       auth_key: Annotated[str, typer.Option(prompt='meta-cache key')],
                       skip_until_id: str | None = None,
                       skip_batches: int = 0,
                       file_ids: Path = Path('../../data/ids.txt'),
                       only_non_oa: bool = False,
                       use_stemming: bool = True,
                       search_fulltext: bool = False,
                       created_since: Annotated[str | None, typer.Option(help='Get works created on or after')] = None,
                       batch_size: int = 200):
    openalex_ids(query=query,
                 file_ids=file_ids,
                 only_non_oa=only_non_oa,
                 use_stemming=use_stemming,
                 search_fulltext=search_fulltext)
    request_ids(solr_host=solr_host, solr_collection=solr_collection,
                auth_key=auth_key, file_ids=file_ids, skip_batches=skip_batches,
                skip_until_id=skip_until_id, batch_size=batch_size)
    push_cache(solr_host=solr_host, solr_collection=solr_collection,
               conf_file=conf_file, created_since=created_since, batch_size=batch_size)


if __name__ == '__main__':
    app()
