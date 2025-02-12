import logging
from pathlib import Path
from typing import Annotated

import httpx
import typer

from meta_cache.handlers.models import Reference
from meta_cache.handlers.util import batched
from meta_cache.handlers.wrappers import DimensionsWrapper, ScopusWrapper
from meta_cache.scripts.config import db_engine_cache

BATCH_SIZE = 500

logger = logging.getLogger('copy')


def main(solr_host: Annotated[str, typer.Option(prompt='host')],
         solr_collection: Annotated[str, typer.Option(prompt='solr collection')],
         ids_file: Annotated[Path, typer.Option(prompt='path to file with ids to check')],
         auth_key: Annotated[str, typer.Option(prompt='meta-cache key')],
         skip_until_id: str | None = None,
         skip_batches: int = 0,
         loglevel: str = 'DEBUG'):
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s (%(process)d): %(message)s', level=loglevel)

    with open(ids_file) as f:
        openalex_ids = list(set([oai_id.strip() for oai_id in f.readlines() if len(oai_id.strip()) > 0]))

    openalex_ids = sorted(openalex_ids)

    found_starting_point = False

    with httpx.Client() as client:
        for bi, batch in enumerate(batched(openalex_ids, BATCH_SIZE)):
            logger.info(f'----------- Processing batch {bi} -----------')
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
                                 'rows': BATCH_SIZE,
                                 'useParams': '',
                                 'defType': 'lucene'
                             }).json()

            if len(res['response']['docs']) == 0:
                logger.debug('Batch has no missing abstracts in solr.')
                continue
            logger.info(f'Missing abstract for {len(res['response']['docs']):,} entries')

            references = [
                Reference(openalex_id=doc['id'], doi=doc['doi'][16:])
                for doc in res['response']['docs']
                if doc.get('doi') is not None
            ]
            if len(references) == 0:
                logger.debug('Batch has no DOIs.')
                continue

            # request dimensions
            cache_response = DimensionsWrapper.run(db_engine=db_engine_cache, references=references, auth_key=auth_key)

            # with remaining request scopus
            remaining = [ref for ref in cache_response.references if ref.missed]
            if len(remaining) > 0:
                logger.info(f'{len(remaining):,} references remaining for scopus')
                cache_response = ScopusWrapper.run(db_engine=db_engine_cache, references=[
                    Reference(openalex_id=doc.openalex_id, doi=doc.doi) for doc in remaining], auth_key=auth_key)
            else:
                logger.debug('Skipping scopus, all ready')

            # with remaining request wos


if __name__ == '__main__':
    typer.run(main)
