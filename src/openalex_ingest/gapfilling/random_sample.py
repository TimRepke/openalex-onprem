from pathlib import Path
from typing import Annotated

import typer
from nacsos_data.util.conf import load_settings

from openalex_ingest.shared.solr import random_sample
from openalex_ingest.shared.util import get_logger


def main(
    target: Annotated[Path, typer.Option(help='Path to file with OpenAlex IDs (stripped, one id per line')],
    config: Annotated[Path, typer.Option(help='Path to config file')],
    batch_size: Annotated[int, typer.Option(help='Batch size for processing')] = 5000,
    target_size: Annotated[int, typer.Option(help='Batch size for processing')] = 10000,
    seed: Annotated[int, typer.Option(help='Batch size for processing')] = 4243,
    include_xpac: Annotated[bool, typer.Option('--include-xpac/--exclude-xpac', help='Include XPAC records in sample')] = False,
    loglevel: Annotated[str, typer.Option(help='Path to config file')] = 'INFO',
):
    logger = get_logger(logger_name='random-sample', run_log_init=True, loglevel=loglevel)

    logger.info(f'Loading config from {config.resolve()}...')
    if not config.exists():
        raise AssertionError(f'Config file does not exist at {config.resolve()}!')
    settings = load_settings(config)
    logger.info(f'Excluding xpac records: {not include_xpac}')

    sample_ids = set()
    it = 0
    while len(sample_ids) < target_size:
        batch_ids = {
            entry['id']
            for entry in random_sample(
                return_fields='id',
                sample_size=min(batch_size, target_size - len(sample_ids)),
                config=settings.OPENALEX,
                ensure_abstract=False,
                include_xpac=include_xpac,
                seed=seed + it,
            )
        }
        sample_ids |= batch_ids
        it += 1
        logger.info(f'Sampled {len(sample_ids):,} IDs after {it:,} iterations, got {len(batch_ids):,} in this batch')

    logger.info(f'Writing sampled IDs to {target}')
    with open(target, 'w') as f:
        for sample_id in sample_ids:
            f.write(sample_id + '\n')

    logger.info('All done.')
