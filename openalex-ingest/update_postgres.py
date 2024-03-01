import logging
from pathlib import Path

import typer
from typing_extensions import Annotated

from processors.postgres.flatten import (
    flatten_authors,
    flatten_concepts,
    flatten_funders,
    flatten_institutions,
    flatten_publishers,
    flatten_sources,
    flatten_works,
    flatten_topics
)


def update_postgres(tmp_dir: Annotated[Path, typer.Option(help='Directory for temporary parsed partition files')],
                    snapshot_dir: Annotated[Path, typer.Option(help='Path to openalex snapshot from S3')],
                    last_update: Annotated[str, typer.Option(help='YYYY-MM-DD of when PG was last updated')],
                    pg_schema: Annotated[str, typer.Option(help='PG schema')],
                    skip_deletion: bool = False,
                    parallelism: int = 8,
                    override: bool = False,
                    preserve_ram: bool = True,
                    loglevel: str = 'INFO'):
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s (%(process)d): %(message)s', level=loglevel)

    logging.info('Please ensure you compiled the cython sources via\n'
                 '   $ python setup.py build_ext --inplace')
    logging.info('Please ensure you synced the snapshot via\n'
                 '   $ aws s3 sync "s3://openalex" "openalex-snapshot" --no-sign-request')

    (tmp_dir / 'postgres').mkdir(parents=True, exist_ok=True)

    logging.info('Flattening topics')
    flatten_topics(tmp_dir=tmp_dir, parallelism=parallelism, skip_deletion=skip_deletion, override=override,
                   preserve_ram=preserve_ram, pg_schema=pg_schema, snapshot_dir=snapshot_dir, last_update=last_update)
    logging.info('Flattening works')
    flatten_works(tmp_dir=tmp_dir, parallelism=parallelism, skip_deletion=skip_deletion, override=override,
                  preserve_ram=preserve_ram, pg_schema=pg_schema, snapshot_dir=snapshot_dir, last_update=last_update)
    logging.info('Flattening authors')
    flatten_authors(tmp_dir=tmp_dir, parallelism=parallelism, skip_deletion=skip_deletion, override=override,
                    preserve_ram=preserve_ram, pg_schema=pg_schema, snapshot_dir=snapshot_dir, last_update=last_update)
    logging.info('Flattening publishers')
    flatten_publishers(tmp_dir=tmp_dir, parallelism=parallelism, skip_deletion=skip_deletion, override=override,
                       preserve_ram=preserve_ram, pg_schema=pg_schema, snapshot_dir=snapshot_dir,
                       last_update=last_update)
    logging.info('Flattening sources')
    flatten_sources(tmp_dir=tmp_dir, parallelism=parallelism, skip_deletion=skip_deletion, override=override,
                    preserve_ram=preserve_ram, pg_schema=pg_schema, snapshot_dir=snapshot_dir, last_update=last_update)
    logging.info('Flattening institutions')
    flatten_institutions(tmp_dir=tmp_dir, parallelism=parallelism, skip_deletion=skip_deletion, override=override,
                         preserve_ram=preserve_ram, pg_schema=pg_schema, snapshot_dir=snapshot_dir,
                         last_update=last_update)
    logging.info('Flattening concepts')
    flatten_concepts(tmp_dir=tmp_dir, parallelism=parallelism, skip_deletion=skip_deletion, override=override,
                     preserve_ram=preserve_ram, pg_schema=pg_schema, snapshot_dir=snapshot_dir, last_update=last_update)
    logging.info('Flattening funders')
    flatten_funders(tmp_dir=tmp_dir, parallelism=parallelism, skip_deletion=skip_deletion, override=override,
                    preserve_ram=preserve_ram, pg_schema=pg_schema, snapshot_dir=snapshot_dir, last_update=last_update)
    logging.info('Postgres files are flattened.')


if __name__ == "__main__":
    typer.run(update_postgres)
