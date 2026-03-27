import gzip
import logging
from pathlib import Path
from typing import Generator

from msgspec import DecodeError
from msgspec.json import Decoder
from nacsos_data.models.openalex import strip_url, invert_abstract
from tqdm import tqdm

from openalex_ingest.shared.util import get_logger
from openalex_ingest.snapshot.match.structs import Work


def read_partition(in_file: str | Path, logger: logging.Logger) -> Generator[tuple[str, str | None], None, None]:
    decoder_work = Decoder(Work)

    with gzip.open(in_file, 'rb') as f_in:
        for li, line in tqdm(enumerate(f_in), desc=f'Processing partition {in_file}'):
            try:
                work = decoder_work.decode(line)
            except Exception as e:
                print(line)
                raise e
            openalex_id = strip_url(work.id)

            abstract = None
            if work.abstract_inverted_index is not None:
                try:
                    abstract = invert_abstract(work.abstract_inverted_index)
                    if len(abstract.strip()) < 1:
                        abstract = None
                except DecodeError:
                    logger.warning(f'Failed to read abstract for {openalex_id} (line {li:,}) in {in_file}')
                    abstract = None
            yield openalex_id, abstract


def read_partitions(snapshot: Path, logger: logging.Logger, seen_file: Path) -> Generator[tuple[str, str | None], None, None]:
    works_files = set(snapshot.glob(f'works/**/*.gz'))
    if seen_file is not None and seen_file.exists():
        with open(seen_file, 'r') as seen_f:
            seen_files = set([Path(line.strip()) for line in seen_f])
        works_files -= seen_files

    logging.info(f'Found there are {len(works_files)} works partitions.')
    with open(seen_file, 'a') as seen_f:
        for fi, work_file in enumerate(sorted(works_files)):
            logger.info(f'Reading {fi:,}/{len(works_files):,} works partition: {work_file}')
            yield from read_partition(work_file, logger)
            seen_f.write(f'{work_file}\n')


if __name__ == '__main__':
    logger_ = get_logger('reader', run_log_init=True)
    nw, na = 0, 0
    for oa_id, abst in read_partitions(Path('data/snapshot/'), logger_, seen_file=Path('data/seen_part.txt')):
        nw += 1
        if abst is None:
            na += 1
    print(nw, na)
