import json
from datetime import datetime
from itertools import batched
from pathlib import Path
from typing import Annotated

import httpx
import typer
from nacsos_data.models.openalex import title_abstract

from openalex_ingest.shared.schema import Request
from openalex_ingest.shared.solr import check_openalex_ids
from openalex_ingest.shared.util import prepare_runner
from openalex_ingest.snapshot.match.reader import read_partitions


def main(
    snapshot: Annotated[Path, typer.Option(help='Path to snapshot')],
    processed_partitions: Annotated[Path, typer.Option(help='Path to memory file to keep track of which partitions are already processed')],
    config: Annotated[Path, typer.Option(help='Path to config file')],
    batch_size: int = 500,
    loglevel: str = 'INFO',
):
    logger, settings, db_engine = prepare_runner(config=config, loglevel=loglevel, logger_name='openalex-backup', run_log_init=True)

    num_works = 0
    num_works_with_abstract = 0
    num_matched_ids = 0
    num_updated = 0
    with db_engine.session() as session:
        for batch in batched(read_partitions(snapshot=snapshot, logger=logger, seen_file=processed_partitions), n=batch_size, strict=False):
            works = {openalex_id: abstract for openalex_id, abstract in batch if abstract is not None}

            num_works += len(batch)
            num_works_with_abstract += len(works)

            if (num_works % 250000) == 0:
                logger.info(
                    f'Processed {num_works:,} so far of which {num_works_with_abstract:,} had an abstract '
                    f'of which {num_matched_ids:,} were found by ID in solr of which {num_updated:,} did not have an abstract in solr',
                )

            if len(works) == 0:
                continue

            ids_matched = check_openalex_ids(settings.OPENALEX, list(works.keys()), check_abstract=False)
            num_matched_ids += len(ids_matched)

            ids_missing_abstract_ = check_openalex_ids(settings.OPENALEX, list(works.keys()))
            ids_missing_abstract = {doc['id']: doc.get('title') for doc in ids_missing_abstract_}
            num_updated += len(ids_missing_abstract)

            if len(ids_missing_abstract) == 0:
                continue

            timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            updates = [
                {
                    'id': openalex_id,
                    # 'title': {'set': record.title},
                    'abstract': {'set': works[openalex_id]},
                    'title_abstract': {'set': title_abstract(title, works[openalex_id])},
                    'abstract_source': {'set': 'OpenAlex_old'},
                    'abstract_date': {'set': timestamp},
                }
                for openalex_id, title in ids_missing_abstract.items()
            ]
            solarized = False
            try:
                res = httpx.post(
                    f'{settings.OPENALEX.solr_url}/update/json?commit=true',
                    headers={'Content-Type': 'application/json'},
                    content=json.dumps(updates),
                    timeout=120,
                )
                res.raise_for_status()
                solarized = True
            except Exception as e:
                logger.error(f'Failed to write to solr: {e}')
                logger.error(res.text)
                # raise e

            session.add_all(
                [
                    Request(
                        wrapper='OpenAlex_old',
                        openalex_id=openalex_id,
                        abstract=works[openalex_id],
                        solarized=solarized,
                    )
                    for openalex_id in ids_missing_abstract.keys()
                ],
            )
            session.commit()

    logger.info(f'Done after processing {num_works:,}  of which {num_works_with_abstract:,} had an abstract of which {num_updated:,} were not in solr')
