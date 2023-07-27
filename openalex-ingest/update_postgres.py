import logging
from pathlib import Path

import typer

from processors.postgres.flatten import flatten_authors
from shared.config import settings
from shared.util import get_globs


def update_postgres(tmp_dir: Path,  # Directory where we can write temporary parsed partition files
                    parallelism: int = 8,
                    loglevel: str = 'INFO'):
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s (%(process)d): %(message)s', level=loglevel)

    logging.info('Please ensure you compiled the cython sources via\n'
                 '   $ python setup.py build_ext --inplace')
    logging.info('Please ensure you synced the snapshot via\n'
                 '   $ aws s3 sync "s3://openalex" "openalex-snapshot" --no-sign-request')

    flatten_authors(tmp_dir=tmp_dir, parallelism=parallelism)

    works, merged_works = get_globs(settings.snapshot, settings.last_update, 'work')
    funders, merged_funders = get_globs(settings.snapshot, settings.last_update, 'funder')
    sources, merged_sources = get_globs(settings.snapshot, settings.last_update, 'source')
    concepts, merged_concepts = get_globs(settings.snapshot, settings.last_update, 'concept')
    publishers, merged_publishers = get_globs(settings.snapshot, settings.last_update, 'publisher')
    institutions, merged_institutions = get_globs(settings.snapshot, settings.last_update, 'institution')

    logging.info('Postgres is up to date.')
    logging.warning(f'Remember to update the date in "{settings.last_update_file}"')


if __name__ == "__main__":
    typer.run(update_postgres)
