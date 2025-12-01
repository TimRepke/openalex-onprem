import gzip
import logging
from pathlib import Path

import tqdm
import httpx
import typer
import orjson as json
from httpx import Client
from nacsos_data.models.openalex import WorksSchema
from nacsos_data.util import batched
from typing_extensions import Annotated
from nacsos_data.util.academic.apis.openalex import translate_work_to_solr
from nacsos_data.util.conf import load_settings


def name_part(partition: Path):
    update = str(partition.parent.name).replace('updated_date=', '')
    return f'{update}-{partition.stem}'


def update_solr(
        snapshot: Annotated[Path, typer.Option(help='Path to openalex snapshot from S3')],
        config_file: Annotated[Path, typer.Option(help='Path to config file')],
        skip_n_partitions: int = 0,
        filter_since: str = '2000-01-01',
        post_batchsize: int = 1000,
        loglevel: str = 'INFO',
) -> None:
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s (%(process)d): %(message)s', level=loglevel)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('root').setLevel(logging.WARNING)

    logging.info(f'Loading config from {config_file.resolve()}...')
    config = load_settings(config_file)
    logging.info(f'Will use solr collection at: {config.OPENALEX.solr_url}')

    logging.info(
        'Please ensure you synced the snapshot via\n'
        '   $  aws s3 sync "s3://openalex/data" "data" --no-sign-request --delete',
    )

    partitions = list(sorted(snapshot.glob(f'data/works/**/*.gz')))
    logging.info(f'Looks like there are {len(partitions):,} partitions.')
    partitions = partitions[skip_n_partitions:]
    logging.info(f'Looks like there are {len(partitions):,} partitions after skipping the first {skip_n_partitions}.')
    partitions = [p for p in partitions if p.parent.name > f'updated_date={filter_since}']
    logging.info(f'Looks like there are {len(partitions):,} partitions after filtering for update >= {filter_since}.')

    progress = tqdm.tqdm(total=len(partitions))
    total = 0
    failed = 0
    for pi, partition in enumerate(partitions, 1):
        progress.set_description_str(f'READ ({pi:,})')
        progress.set_postfix_str(f'total={total:,}, failed={failed:,}, partition={'/'.join(partition.parts[-2:])}')

        with gzip.open(partition, 'rb') as f_in:
            works = [json.dumps(translate_work_to_solr(WorksSchema.model_validate(json.loads(line)))) for line in f_in]

        progress.set_description_str(f'LOAD ({pi:,})')
        progress.set_postfix_str(f'total={total:,}, failed={failed:,}, size={len(works):,}, partition={'/'.join(partition.parts[-2:])}')

        with Client(auth=config.OPENALEX.auth, timeout=120, headers={'Content-Type': 'application/json'}) as solr:

            for bi, batch in enumerate(batched(works, batch_size=post_batchsize)):
                res = solr.post(
                    f'{config.OPENALEX.SOLR_ENDPOINT}/api/collections/{config.OPENALEX.SOLR_COLLECTION}/update/json?commit=true',
                    data=b'\n'.join(batch).decode(),
                )
                try:
                    res.raise_for_status()
                except httpx.HTTPError as e:
                    logging.exception(e)
                    failed += len(batch)

                progress.set_description_str(f'LOAD ({pi:,}) | {bi*post_batchsize:,}/{len(works):,}')

        total += len(works)

    logging.info('Finished loading partitions!')


if __name__ == "__main__":
    typer.run(update_solr)
