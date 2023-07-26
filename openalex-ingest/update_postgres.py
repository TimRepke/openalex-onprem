import logging
from pathlib import Path
from util import get_globs
import typer


def update_pg(snapshot: Path,  # /path/to/openalex-snapshot/
              last_update: str,  # formatted as YYYY-MM-DD
              loglevel='INFO'):
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s (%(process)d): %(message)s', level=loglevel)

    logging.info('Please ensure you synced the snapshot via\n'
                 '   $ aws s3 sync "s3://openalex" "openalex-snapshot" --no-sign-request')

    works, merged = get_globs(snapshot, last_update, 'works')

    logging.info(f'Looks like there are {len(works)} works partitions '
                 f'and {len(merged)} merged_ids partitions since last update.')

    for partition in works:
        pass

    # merge_date,id,merge_into_id


if __name__ == "__main__":
    typer.run(update_pg)
