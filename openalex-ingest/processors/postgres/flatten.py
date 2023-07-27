import logging
import multiprocessing
from pathlib import Path

from processors.postgres.deletion import generate_deletions_from_merge_file
from shared.config import settings
from shared.util import get_globs

from processors.postgres.flatten_partition import flatten_authors_partition


def flatten_authors(tmp_dir: Path, parallelism: int = 8, ):
    authors, merged_authors = get_globs(settings.snapshot, settings.last_update, 'author')

    logging.info(f'Looks like there are {len(authors)} author partitions '
                 f'and {len(merged_authors)} merged_ids partitions since last update.')
    author_params = [
        {
            'partition': partition,
            'out_sql_cpy': tmp_dir / f'pg-author-{partition.parent.name}-{partition.stem}-cpy.sql',
            'out_sql_del': tmp_dir / f'pg-author-{partition.parent.name}-{partition.stem}-del.sql',
            'out_authors': tmp_dir / f'pg-author-{partition.parent.name}-{partition.stem}_authors.csv.gz',
            'out_m2m_institution': tmp_dir / f'pg-author-{partition.parent.name}-{partition.stem}_author_institutions.csv.gz'
        }
        for partition in authors
    ]
    if parallelism == 1:
        for ap in author_params:
            flatten_authors_partition(**ap)
    else:
        with multiprocessing.Pool(parallelism) as pool:
            pool.apply(lambda params: flatten_authors_partition(**params), author_params)

    generate_deletions_from_merge_file(merge_files=merged_authors,
                                       out_file=tmp_dir / f'pg-author-merged-del.sql',
                                       object_type='author',
                                       batch_size=1000)
