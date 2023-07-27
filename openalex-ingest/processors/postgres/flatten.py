import logging
import multiprocessing
from pathlib import Path

from shared.config import settings
from shared.util import get_globs

from processors.postgres.deletion import generate_deletions_from_merge_file
from processors.postgres.flatten_partition import flatten_authors_partition, flatten_institutions_partition, \
    flatten_funder_partition, flatten_concept_partition, flatten_works_partition, flatten_publisher_partition, \
    flatten_sources_partition


def run(func, params, parallelism: int):
    if parallelism == 1:
        for kwargs in params:
            func(**kwargs)
    else:
        with multiprocessing.Pool(parallelism) as pool:
            pool.apply(lambda kwargs: func(**kwargs), params)


def name_part(partition: Path):
    update = str(partition.parent.name).replace('updated_date=', '')
    return f'{update}-{partition.stem}'


def flatten_authors(tmp_dir: Path, parallelism: int = 8):
    authors, merged_authors = get_globs(settings.snapshot, settings.last_update, 'author')

    logging.info(f'Looks like there are {len(authors)} author partitions '
                 f'and {len(merged_authors)} merged_ids partitions since last update.')
    run(flatten_authors_partition,
        [
            {
                'partition': partition,
                'out_sql_cpy': tmp_dir / f'pg-author-{name_part(partition)}-cpy.sql',
                'out_sql_del': tmp_dir / f'pg-author-{name_part(partition)}-del.sql',
                'out_authors': tmp_dir / f'pg-author-{name_part(partition)}_authors.csv.gz',
                'out_m2m_institution': tmp_dir / f'pg-author-{name_part(partition)}_author_institutions.csv.gz'
            }
            for partition in authors
        ], parallelism=parallelism)

    generate_deletions_from_merge_file(merge_files=merged_authors,
                                       out_file=tmp_dir / f'pg-author-{settings.last_update}-merged_del.sql',
                                       object_type='author',
                                       batch_size=1000)


def flatten_institutions(tmp_dir: Path, parallelism: int = 8):
    partitions, merged = get_globs(settings.snapshot, settings.last_update, 'institution')
    logging.info(f'Looks like there are {len(partitions)} institution partitions '
                 f'and {len(merged)} merged_ids partitions since last update.')
    run(flatten_institutions_partition,
        [
            {
                'partition': partition,
                'out_sql_cpy': tmp_dir / f'pg-institution-{name_part(partition)}-cpy.sql',
                'out_sql_del': tmp_dir / f'pg-institution-{name_part(partition)}-del.sql',
                'out_institutions': tmp_dir / f'pg-institution-{name_part(partition)}_institution.csv.gz',
                'out_m2m_association': tmp_dir / f'pg-institution-{name_part(partition)}_institution_associations.csv.gz',
                'out_m2m_concepts': tmp_dir / f'pg-institution-{name_part(partition)}_institution_concepts.csv.gz'
            }
            for partition in partitions
        ], parallelism=parallelism)

    generate_deletions_from_merge_file(merge_files=merged,
                                       out_file=tmp_dir / f'pg-institution-{settings.last_update}-merged_del.sql',
                                       object_type='institution',
                                       batch_size=1000)


def flatten_publishers(tmp_dir: Path, parallelism: int = 8):
    partitions, merged = get_globs(settings.snapshot, settings.last_update, 'publisher')
    logging.info(f'Looks like there are {len(partitions)} publisher partitions '
                 f'and {len(merged)} merged_ids partitions since last update.')
    run(flatten_institutions_partition,
        [
            {
                'partition': partition,
                'out_sql_cpy': tmp_dir / f'pg-publisher-{name_part(partition)}-cpy.sql',
                'out_sql_del': tmp_dir / f'pg-publisher-{name_part(partition)}-del.sql',
                'out_publishers': tmp_dir / f'pg-publisher-{name_part(partition)}_publishers.csv.gz',
            }
            for partition in partitions
        ], parallelism=parallelism)

    generate_deletions_from_merge_file(merge_files=merged,
                                       out_file=tmp_dir / f'pg-publisher-{settings.last_update}-merged_del.sql',
                                       object_type='publisher',
                                       batch_size=1000)


def flatten_funders(tmp_dir: Path, parallelism: int = 8):
    partitions, merged = get_globs(settings.snapshot, settings.last_update, 'funder')
    logging.info(f'Looks like there are {len(partitions)} funder partitions '
                 f'and {len(merged)} merged_ids partitions since last update.')
    run(flatten_funder_partition,
        [
            {
                'partition': partition,
                'out_sql_cpy': tmp_dir / f'pg-funder-{name_part(partition)}-cpy.sql',
                'out_sql_del': tmp_dir / f'pg-funder-{name_part(partition)}-del.sql',
                'out_funders': tmp_dir / f'pg-funder-{name_part(partition)}_funders.csv.gz',
            }
            for partition in partitions
        ], parallelism=parallelism)

    generate_deletions_from_merge_file(merge_files=merged,
                                       out_file=tmp_dir / f'pg-funder-{settings.last_update}-merged_del.sql',
                                       object_type='funder',
                                       batch_size=1000)


def flatten_concepts(tmp_dir: Path, parallelism: int = 8):
    partitions, merged = get_globs(settings.snapshot, settings.last_update, 'concept')
    logging.info(f'Looks like there are {len(partitions)} concepts partitions '
                 f'and {len(merged)} merged_ids partitions since last update.')
    run(flatten_concept_partition,
        [
            {
                'partition': partition,
                'out_sql_cpy': tmp_dir / f'pg-concept-{name_part(partition)}-cpy.sql',
                'out_sql_del': tmp_dir / f'pg-concept-{name_part(partition)}-del.sql',
                'out_concepts': tmp_dir / f'pg-concept-{name_part(partition)}_concepts.csv.gz',
                'out_m2m_ancestor': tmp_dir / f'pg-concept-{name_part(partition)}_concepts_ancestor.csv.gz',
                'out_m2m_related': tmp_dir / f'pg-concept-{name_part(partition)}_concepts_related.csv.gz',
            }
            for partition in partitions
        ], parallelism=parallelism)

    generate_deletions_from_merge_file(merge_files=merged,
                                       out_file=tmp_dir / f'pg-concept-{settings.last_update}-merged_del.sql',
                                       object_type='concept',
                                       batch_size=1000)


def flatten_sources(tmp_dir: Path, parallelism: int = 8):
    partitions, merged = get_globs(settings.snapshot, settings.last_update, 'source')
    logging.info(f'Looks like there are {len(partitions)} source partitions '
                 f'and {len(merged)} merged_ids partitions since last update.')
    run(flatten_sources_partition,
        [
            {
                'partition': partition,
                'out_sql_cpy': tmp_dir / f'pg-source-{name_part(partition)}-cpy.sql',
                'out_sql_del': tmp_dir / f'pg-source-{name_part(partition)}-del.sql',
                'out_sources': tmp_dir / f'pg-source-{name_part(partition)}_sources.csv.gz',
            }
            for partition in partitions
        ], parallelism=parallelism)

    generate_deletions_from_merge_file(merge_files=merged,
                                       out_file=tmp_dir / f'pg-source-{settings.last_update}-merged_del.sql',
                                       object_type='source',
                                       batch_size=1000)


def flatten_works(tmp_dir: Path, parallelism: int = 8):
    partitions, merged = get_globs(settings.snapshot, settings.last_update, 'work')
    logging.info(f'Looks like there are {len(partitions)} works partitions '
                 f'and {len(merged)} merged_ids partitions since last update.')
    run(flatten_works_partition,
        [
            {
                'partition': partition,
                'out_sql_cpy': tmp_dir / f'pg-work-{name_part(partition)}-cpy.sql',
                'out_sql_del': tmp_dir / f'pg-work-{name_part(partition)}-del.sql',
                'out_works': tmp_dir / f'pg-work-{name_part(partition)}_works.csv.gz',
                'out_m2m_locations': tmp_dir / f'pg-work-{name_part(partition)}_works_locations.csv.gz',
                'out_m2m_concepts': tmp_dir / f'pg-work-{name_part(partition)}_works_concepts.csv.gz',
                'out_m2m_authorships': tmp_dir / f'pg-work-{name_part(partition)}_works_authorships.csv.gz',
                'out_m2m_references': tmp_dir / f'pg-work-{name_part(partition)}_works_references.csv.gz',
                'out_m2m_related': tmp_dir / f'pg-work-{name_part(partition)}_works_related.csv.gz',
            }
            for partition in partitions
        ], parallelism=parallelism)

    generate_deletions_from_merge_file(merge_files=merged,
                                       out_file=tmp_dir / f'pg-work-{settings.last_update}-merged_del.sql',
                                       object_type='work',
                                       batch_size=1000)
