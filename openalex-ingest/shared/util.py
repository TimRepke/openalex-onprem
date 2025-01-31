import gzip
import logging
from pathlib import Path
from time import perf_counter, sleep
from contextlib import ContextDecorator
from typing import Literal, Generator, Iterable

ObjectType = Literal['work', 'author', 'funder', 'publisher', 'source',
'institution', 'concept', 'topic', 'subfield', 'field', 'domain']


def get_globs(snapshot: Path,  # /path/to/openalex-snapshot
              filter_since: str = '2020-01-01',
              obj_type: ObjectType = 'work') -> tuple[list[Path], list[Path]]:
    return (sorted([p
                    for p in snapshot.glob(f'data/{obj_type}s/**/*.gz')
                    if p.parent.name > f'updated_date={filter_since}']),
            sorted([m
                    for m in snapshot.glob(f'data/merged_ids/{obj_type}s/*.csv.gz')
                    if m.name > f'{filter_since}.csv.gz']))


def get_ids_to_delete(merge_files: list[Path]) -> Generator[str, None, None]:
    import csv
    for file in merge_files:
        with gzip.open(file, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            next(reader)  # skip header: merge_date,id,merge_into_id
            yield from [
                row[1]
                for row in reader
            ]


def strip_id(s: str | None) -> str | None:
    if s is not None and len(s) > 20:
        if len(s) > 20:
            return s[21:]
        if len(s) > 0:
            return s
    return None


def parse_id(s: str | None, prefix: str) -> int | None:
    if s is not None and len(s) > len(prefix):
        return int(s[len(prefix):])
    return None


def batched(it: Iterable[str], bs: int) -> Generator[list[str], None, None]:
    batch = []
    cnt = 0
    for i in it:
        batch.append(i)
        cnt += 1
        if cnt > bs:
            yield batch
            batch = []
            cnt = 0
    yield batch


class rate_limit(ContextDecorator):
    def __init__(self, min_time_ms: int = 100):
        self.min_time = min_time_ms / 1000

    def __enter__(self):
        self.start = perf_counter()
        return self

    def __exit__(self, type, value, traceback):
        self.time = perf_counter() - self.start
        self.readout = f'Time: {self.time:.3f} seconds'
        if self.time < self.min_time:
            logging.debug(f'Sleeping to keep rate limit: {self.min_time - self.time:.4f} seconds')
            sleep(self.min_time - self.time)
