import logging
from pathlib import Path

import typer

from processors.postgres.flatten import flatten_authors, flatten_concepts, flatten_funders, flatten_institutions, \
    flatten_publishers, flatten_sources, flatten_works
from shared.config import settings


def update_postgres(tmp_dir: Path,  # Directory where we can write temporary parsed partition files
                    skip_deletion: bool = False,
                    parallelism: int = 8,
                    loglevel: str = 'INFO'):
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s (%(process)d): %(message)s', level=loglevel)

    logging.info('Please ensure you compiled the cython sources via\n'
                 '   $ python setup.py build_ext --inplace')
    logging.info('Please ensure you synced the snapshot via\n'
                 '   $ aws s3 sync "s3://openalex" "openalex-snapshot" --no-sign-request')

    (tmp_dir / 'postgres').mkdir(parents=True, exist_ok=True)

    logging.info('Flattening publishers')
    flatten_publishers(tmp_dir=tmp_dir, parallelism=parallelism, skip_deletion=skip_deletion)
    logging.info('Flattening sources')
    flatten_sources(tmp_dir=tmp_dir, parallelism=parallelism, skip_deletion=skip_deletion)
    logging.info('Flattening institutions')
    flatten_institutions(tmp_dir=tmp_dir, parallelism=parallelism, skip_deletion=skip_deletion)
    logging.info('Flattening concepts')
    flatten_concepts(tmp_dir=tmp_dir, parallelism=parallelism, skip_deletion=skip_deletion)
    logging.info('Flattening funders')
    flatten_funders(tmp_dir=tmp_dir, parallelism=parallelism, skip_deletion=skip_deletion)
    logging.info('Flattening authors')
    flatten_authors(tmp_dir=tmp_dir, parallelism=parallelism, skip_deletion=skip_deletion)
    logging.info('Flattening works')
    flatten_works(tmp_dir=tmp_dir, parallelism=parallelism, skip_deletion=skip_deletion)

    logging.info('Postgres is up to date.')
    logging.warning(f'Remember to update the date in "{settings.last_update_file}"')


if __name__ == "__main__":
    typer.run(update_postgres)
