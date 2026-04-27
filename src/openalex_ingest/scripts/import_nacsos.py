from itertools import batched
from pathlib import Path
from typing import Annotated
from tqdm import tqdm

import typer
import sqlalchemy as sa

from openalex_ingest.shared.db import get_engine, DatabaseEngine
from openalex_ingest.shared.schema import Request
from openalex_ingest.shared.util import prepare_runner


def read_nacsos_abstracts(db_engine: DatabaseEngine, min_len: int = 1000, batch_size: int = 100):
    with db_engine.session() as session:
        partitions = (
            session.execute(
                sa.text(
                    """
                    SELECT 'NACSOS'  as wrapper,
                           i.item_id as nacsos_id,
                           ai.doi,
                           ai.wos_id,
                           ai.scopus_id,
                           ai.openalex_id,
                           ai.s2_id,
                           ai.pubmed_id,
                           ai.dimensions_id,
                           ai.title,
                           i.text    as abstract,
                           jsonb_build_object(
                                   'meta', ai.meta - 'places',
                                   'project_id', i.project_id,
                                   'publication_year', ai.publication_year
                           )         as raw
                    FROM item i
                         LEFT JOIN academic_item ai ON ai.item_id = i.item_id
                    WHERE i.text IS NOT NULL
                      AND ai.openalex_id IS NOT NULL
                      --AND length(i.text) > :min_len;
                    """
                ),
                params={'min_len': min_len},
                execution_options={'yield_per': batch_size},
            )
            .mappings()
            .partitions(batch_size)
        )

        for partition in partitions:
            yield from partition


def main(
    config: Annotated[Path, typer.Option(help='Path to config file')],
    bs_read: Annotated[int, typer.Option(help='Batch size for processing')] = 500,
    bs_write: Annotated[int, typer.Option(help='Batch size for processing')] = 100,
    min_len: Annotated[int, typer.Option(help='Minimum abstract length to transfer')] = 100,
    loglevel: Annotated[str, typer.Option(help='Path to config file')] = 'INFO',
):
    logger, settings, db_engine = prepare_runner(config=config, loglevel=loglevel, logger_name='openalex-backup', run_log_init=True, db_debug=False)
    db_engine_nacsos = get_engine(settings=settings.DB, debug=False)

    logger.info(f'Proceeding to transfer abstracts from NACSOS to the meta-cache')
    logger.info('If you need to forward a remote port, maybe this helps:')
    logger.info('  (with one jump)   ssh -N -J ts01 -L 5000:localhost:5432 se164')
    logger.info('  (directly)        ssh -N -L 5000:localhost:5432 se164')

    n_tested = 0
    n_added = 0
    progress = tqdm()
    with db_engine.session() as session:
        for batch in batched(read_nacsos_abstracts(db_engine=db_engine_nacsos, batch_size=bs_read, min_len=min_len), bs_write):
            known_records = (
                session.execute(
                    sa.text("""
                SELECT record_id, nacsos_id
                FROM request
                WHERE nacsos_id = ANY(:nacsos_ids) AND abstract IS NOT NULL
            """),
                    {'nacsos_ids': [record['nacsos_id'] for record in batch]},
                )
                .mappings()
                .all()
            )
            known_records = list(known_records)
            known_ids = {record['nacsos_id'] for record in known_records}

            try:
                session.add_all([Request(**record) for record in batch if record['nacsos_id'] not in known_ids and len(record['abstract']) > min_len])
                session.commit()
            except Exception as e:
                for record in batch:
                    logger.warning(record)
                raise e

            n_tested += len(batch)
            n_added += len(batch) - len(known_ids)
            progress.set_postfix_str(f'Added {n_added} / {n_tested} records')
            progress.update(len(batch))
    progress.close()
    logger.info(f'Tested {n_tested:,} records and transferred {n_added:,} records')


if __name__ == '__main__':
    typer.run(main)
