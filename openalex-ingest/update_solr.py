import logging
import subprocess
from io import BytesIO
from pathlib import Path

import httpx
import typer
from typing_extensions import Annotated

from meta_cache.handlers.util import post2solr
from shared.util import get_globs
from processors.solr.transform_partition import transform_partition


def name_part(partition: Path):
    update = str(partition.parent.name).replace('updated_date=', '')
    return f'{update}-{partition.stem}'


def update_solr(tmp_dir: Annotated[Path, typer.Option(help='Directory for temporary parsed partition files')],
                snapshot_dir: Annotated[Path, typer.Option(help='Path to openalex snapshot from S3')],
                solr_collection: Annotated[str, typer.Option(help='Name of the Solr collection')],
                solr_host: Annotated[str, typer.Option(help='Solr hostname')],
                solr_port: Annotated[int, typer.Option(help='Solr port')],
                last_solr_update: Annotated[str, typer.Option(help='YYYY-MM-DD of when solr was last updated')],
                skip_deletion: bool = False,
                skip_n_partitions: int = 0,
                loglevel: str = 'INFO'):
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s (%(process)d): %(message)s', level=loglevel)

    logging.info('Please ensure you compiled the cython sources via\n'
                 '   $ python setup.py build_ext --inplace')
    logging.info('Please ensure you synced the snapshot via\n'
                 '   $ aws s3 sync "s3://openalex" "openalex-snapshot" --no-sign-request')

    logging.info(f'Looking for files younger than "{last_solr_update}" '
                 f'in snapshot folder at "{snapshot_dir}"')

    works, merged = get_globs(snapshot_dir, last_solr_update, 'work')

    logging.info(f'Looks like there are {len(works)} works partitions '
                 f'and {len(merged)} merged_ids partitions since last update.')

    for pi, partition in enumerate(works, 1):
        if pi <= skip_n_partitions:
            logging.debug(f'Skipping partition {pi}: {partition}')
            continue

        logging.debug(f'Reading partition from: {partition}')
        buffer = BytesIO()
        n_works, n_abstracts = transform_partition(partition, output=buffer)
        logging.info(f'({pi:,}/{len(works):,}) Partition contained {n_works:,} works '
                     f'with {n_abstracts:,} abstracts (referring to {partition})')

        buffer.seek(0)

        res = httpx.post((f'{solr_host}/api/collections/{solr_collection}/update/json?commit=true'),
                         headers={'Content-Type': 'application/json'},
                         data=buffer.read().decode(),
                         timeout=120)
        logging.info(f'Partition posted to solr: {res.status_code}!')
        try:
            res.raise_for_status()
        except httpx.HTTPError as e:
            logging.exception(e)

    logging.info('Solr collection is up to date.')


if __name__ == "__main__":
    typer.run(update_solr)

# Deprecated bit of code. Keeping it in case we ever want to use it again.
# This will assume we keep the existing collection and override documents,
# then we'll have to delete the ones that openalex deleted.
#
# if not skip_deletion and len(merged) > 0:
#     logging.info('Going to delete merged works objects in batches...')
#     for del_batch in batched(get_ids_to_delete(merged), 1000):
#         ids = '</id><id>'.join(del_batch)
#         payload = f'<delete><id>{ids}</id></delete>'
#
#         subprocess.run([settings.solr_bin / 'post',
#                         '-c', solr_collection,
#                         '-commit', 'yes',
#                         '-host', settings.solr_host,
#                         '-port', str(settings.solr_port),
#                         '-d', payload])
# else:
#     logging.info('Found no merged work objects since last update and/or was asked to skip deletions!')
