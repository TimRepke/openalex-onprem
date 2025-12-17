import gzip
import logging
from pathlib import Path

import ujson as json
import tqdm

import typer


def run(
        snapshot: Path,
        target: Path,
) -> None:
    partitions = list(sorted(snapshot.glob(f'data/works/**/*.gz')))
    logging.info(f'Looks like there are {len(partitions):,} partitions.')
    logging.getLogger('root').setLevel(logging.WARNING)

    progress = tqdm.tqdm(total=len(partitions))

    n_total = 0
    n_failed = 0
    with open(target, 'w') as f_out:
        for pi, partition in enumerate(partitions, 1):
            progress.set_postfix_str(
                f'total={n_total:,}, '
                f'failed={n_failed:,}, '
                f'filesize={partition.stat().st_size / 1024 / 1024 / 1024:,.2f}GB, '
                f'partition={'/'.join(partition.parts[-2:])}',
            )

            with gzip.open(partition, 'rb') as f_in:
                progress.set_description_str(f'READ ({pi:,})')
                ids = [json.loads(line)['id'][len('https://openalex.org/'):] for line in f_in]
                f_out.write('\n'.join(ids) + '\n')
            progress.update()


if __name__ == '__main__':
    typer.run(run)
