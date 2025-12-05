import gzip
import logging
from pathlib import Path
from time import sleep

import tqdm
import httpx
import typer
import orjson as json
from httpx import Client
from nacsos_data.models.openalex import WorksSchema
from nacsos_data.util import batched
from typing_extensions import Annotated
from nacsos_data.util.academic.apis.openalex import translate_work_to_solr
from nacsos_data.util.conf import load_settings, OpenAlexConfig


def name_part(partition: Path):
    update = str(partition.parent.name).replace('updated_date=', '')
    return f'{update}-{partition.stem}'


def commit(conf: OpenAlexConfig):
    try:
        httpx.post(f'{conf.SOLR_ENDPOINT}/api/collections/{conf.SOLR_COLLECTION}/update/json?commit=true', timeout=120, auth=conf.auth)
    except Exception as e:
        logging.warning(f'Timed out on commit ({e})')


def update_solr(
        snapshot: Annotated[Path, typer.Option(help='Path to openalex snapshot from S3')],
        config_file: Annotated[Path, typer.Option(help='Path to config file')],
        skip_n_partitions: int = 0,
        filter_since: str = '2000-01-01',
        post_batchsize: int = 1000,
        read_batchsize: int = 50000,
        commit_interval: int = -1,
        max_retry: int = 10,
        loglevel: str = 'INFO',
) -> None:
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s (%(process)d): %(message)s', level=loglevel)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('root').setLevel(logging.DEBUG)

    logging.info(f'Loading config from {config_file.resolve()}...')
    if not config_file.exists():
        raise AssertionError(f'Config file does not exist at {config_file.resolve()}!')
    config = load_settings(config_file)
    logging.info(f'Will use solr collection at: {config.OPENALEX.solr_url}')

    logging.info(
        'Please ensure you synced the snapshot via\n'
        '   $  aws s3 sync "s3://openalex/data" "data" --no-sign-request --delete',
    )

    partitions = list(sorted(snapshot.glob(f'data/works/**/*.gz')))
    logging.info(f'Looks like there are {len(partitions):,} partitions.')
    partitions = [p for p in partitions if p.parent.name >= f'updated_date={filter_since}']
    logging.info(f'Looks like there are {len(partitions):,} partitions after filtering for update >= {filter_since}.')
    partitions = partitions[skip_n_partitions:]
    logging.info(f'Looks like there are {len(partitions):,} partitions after skipping the next {skip_n_partitions}.')

    logging.getLogger('root').setLevel(logging.WARNING)

    progress = tqdm.tqdm(total=len(partitions))

    n_total = 0
    n_failed = 0
    n_uncommited = 0

    for pi, partition in enumerate(partitions, 1):
        progress.set_postfix_str(
            f'total={n_total:,}, '
            f'failed={n_failed:,}, '
            f'filesize={partition.stat().st_size / 1024 / 1024 / 1024:,.2f}GB, '
            f'partition={'/'.join(partition.parts[-2:])}',
        )

        with gzip.open(partition, 'rb') as f_in:
            n_read = 0
            n_posted = 0
            progress.set_description_str(f'READ ({pi:,} | -- | --)')

            for bi, batch in enumerate(batched(f_in, batch_size=read_batchsize)):

                works = [json.dumps(translate_work_to_solr(WorksSchema.model_validate(json.loads(line)))) for line in batch]
                n_read += len(works)
                n_total += len(works)
                n_uncommited += len(works)

                progress.set_description_str(f'POST ({pi:,} | {n_read:,} | {n_posted:,})')

                for post_works in batched(works, batch_size=post_batchsize):
                    for retry in range(max_retry):
                        res = httpx.post(
                            f'{config.OPENALEX.SOLR_ENDPOINT}/api/collections/{config.OPENALEX.SOLR_COLLECTION}/update/json',  # ?overwrite=true',
                            data=b'\n'.join(post_works).decode(),
                            auth=config.OPENALEX.auth,
                            timeout=240,
                            headers={'Content-Type': 'application/json'},
                        )
                        try:
                            res.raise_for_status()
                            n_posted += len(post_works)
                            progress.set_description_str(f'POST ({pi:,} | {n_read:,} | {n_posted:,})')
                            break
                        except Exception as e:
                            if retry < (max_retry - 1):
                                logging.error(e)
                                logging.warning(f'Will try again in {retry * 60} seconds...')
                                sleep(retry * 60)
                            else:
                                n_failed += len(post_works)
                                # raise e

                    if (commit_interval > 0) and (n_uncommited >= commit_interval):
                        commit(config.OPENALEX)
                        n_uncommited = 0

                progress.set_description_str(f'READ ({pi:,} | {n_read:,} | {n_posted:,})')

        progress.update()

    commit(config.OPENALEX)

    logging.info('Finished loading partitions!')


if __name__ == "__main__":
    typer.run(update_solr)
