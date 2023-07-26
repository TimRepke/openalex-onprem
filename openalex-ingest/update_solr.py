import logging
import subprocess
from pathlib import Path

import typer

from config import settings
from util import get_globs, get_ids_to_delete, batched
from transform_partition_solr import transform_partition


def update_solr(tmp_dir: Path,  # Directory where we can write temporary parsed partition files
                loglevel='INFO'):
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s (%(process)d): %(message)s', level=loglevel)

    logging.info('Please ensure you compiled the cython sources via\n'
                 '   $ python setup.py build_ext --inplace')
    logging.info('Please ensure you synced the snapshot via\n'
                 '   $ aws s3 sync "s3://openalex" "openalex-snapshot" --no-sign-request')

    works, merged = get_globs(settings.snapshot, settings.last_update, 'works')

    logging.info(f'Looks like there are {len(works)} works partitions '
                 f'and {len(merged)} merged_ids partitions since last update.')

    for partition in works:
        out_file = tmp_dir / partition.parent.name / f'{partition.stem}.json'
        out_file.parent.mkdir(exist_ok=True, parents=True)

        logging.debug(f'Reading partition from "{partition}" and writing to "{out_file}"')
        n_works, n_abstracts = transform_partition(partition, out_file)
        logging.info(f'Partition contained {n_works} works with {n_abstracts} abstracts (referring to {partition})')

        subprocess.run([settings.solr_bin / 'post',
                        '-c', settings.collection,
                        '-commit', 'yes',
                        '-host', settings.solr_host,
                        '-port', settings.solr_port,
                        out_file])

        logging.info('Partition posted to solr!')

        # Cleaning up (this may leave empty directories though)
        out_file.unlink()

    # Final cleanup
    tmp_dir.unlink()  # FIXME this is not good for parallelisation

    if len(merged) > 0:
        logging.info('Going to delete merged works objects in batches...')
        for del_batch in batched(get_ids_to_delete(merged), 1000):
            ids = '</id><id>'.join(del_batch)
            payload = f'<delete><id>{ids}</id></delete>'

            subprocess.run([settings.solr_bin / 'post',
                            '-c', settings.collection,
                            '-commit', 'yes',
                            '-host', settings.solr_host,
                            '-port', settings.solr_port,
                            '-d', payload])
    else:
        logging.info('Found no merged work objects since last update!')

    logging.info('Solr collection is up to date.')
    logging.warning(f'Remember to update the date in "{settings.last_update_file}"')


if __name__ == "__main__":
    typer.run(update_solr)
