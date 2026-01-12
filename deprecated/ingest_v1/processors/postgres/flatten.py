import logging
import multiprocessing
from pathlib import Path

from shared.util import get_globs

from processors.postgres.deletion import generate_deletions_from_merge_file
from processors.postgres.flatten_partition import (
    flatten_authors_partition_kw,
    flatten_institutions_partition_kw,
    flatten_funders_partition_kw,
    flatten_concepts_partition_kw,
    flatten_works_partition_kw,
    flatten_publishers_partition_kw,
    flatten_sources_partition_kw,
    flatten_topics_partition_kw,
    flatten_subfields_partition_kw,
    flatten_fields_partition_kw,
    flatten_domains_partition_kw
)


def picklify(params):
    return [
        {
            # Path cannot be pickled, so stringify them
            k: (str(v) if isinstance(v, Path) else v)
            for k, v in p.items()
        }
        for p in params
    ]


def all_exist(kwargs: dict):
    # check if all kwargs of type Path already exist as a non-empty file
    return all([
        value.exists() and value.stat().st_size > 100
        for arg, value in kwargs.items()
        if isinstance(value, Path) and arg != 'partition'
    ])


def run(func, params: list[dict], parallelism: int, override: bool):
    if not override:
        params = [kwargs for kwargs in params if not all_exist(kwargs)]
    if len(params) > 0:
        if parallelism == 1:
            for kwargs in params:
                func(kwargs)
        else:
            with multiprocessing.Pool(parallelism) as pool:
                pool.map(func, picklify(params))


def name_part(partition: Path):
    update = str(partition.parent.name).replace('updated_date=', '')
    return f'{update}-{partition.stem}'


def flatten_authors(tmp_dir: Path, snapshot_dir: Path, last_update: str, pg_schema: str, parallelism: int = 8,
                    skip_deletion: bool = False,
                    override: bool = False, preserve_ram: bool = True):
    authors, merged_authors = get_globs(snapshot_dir, last_update, 'author')

    logging.info(f'Looks like there are {len(authors):,} author partitions '
                 f'and {len(merged_authors):,} merged_ids partitions since last update ({last_update}).')
    run(flatten_authors_partition_kw,
        [
            {
                'partition': partition,
                'out_sql_cpy': tmp_dir / f'pg-author-{name_part(partition)}-cpy.sql',
                'out_sql_del': tmp_dir / f'pg-author-{name_part(partition)}-del.sql',
                'out_authors': tmp_dir / f'pg-author-{name_part(partition)}_authors.csv.gz',
                'preserve_ram': preserve_ram,
                'pg_schema': pg_schema
            }
            for partition in authors
        ], parallelism=parallelism, override=override)
    if not skip_deletion:
        generate_deletions_from_merge_file(merge_files=merged_authors,
                                           out_file=tmp_dir / f'pg-author-{last_update}-merged_del.sql',
                                           object_type='author',
                                           pg_schema=pg_schema,
                                           batch_size=1000)


def flatten_institutions(tmp_dir: Path, snapshot_dir: Path, last_update: str, pg_schema: str, parallelism: int = 8,
                         skip_deletion: bool = False,
                         override: bool = False, preserve_ram: bool = True):
    partitions, merged = get_globs(snapshot_dir, last_update, 'institution')
    logging.info(f'Looks like there are {len(partitions):,} institution partitions '
                 f'and {len(merged):,} merged_ids partitions since last update ({last_update}).')
    run(flatten_institutions_partition_kw,
        [
            {
                'partition': partition,
                'out_sql_cpy': tmp_dir / f'pg-institution-{name_part(partition)}-cpy.sql',
                'out_sql_del': tmp_dir / f'pg-institution-{name_part(partition)}-del.sql',
                'out_institutions': tmp_dir / f'pg-institution-{name_part(partition)}_institution.csv.gz',
                'out_m2m_association': tmp_dir / f'pg-institution-{name_part(partition)}_institution_associations.csv.gz',
                'out_m2m_concepts': tmp_dir / f'pg-institution-{name_part(partition)}_institution_concepts.csv.gz',
                'preserve_ram': preserve_ram,
                'pg_schema': pg_schema
            }
            for partition in partitions
        ], parallelism=parallelism, override=override)

    if not skip_deletion:
        generate_deletions_from_merge_file(merge_files=merged,
                                           out_file=tmp_dir / f'pg-institution-{last_update}-merged_del.sql',
                                           object_type='institution',
                                           pg_schema=pg_schema,
                                           batch_size=1000)


def flatten_publishers(tmp_dir: Path, snapshot_dir: Path, last_update: str, pg_schema: str, parallelism: int = 8,
                       skip_deletion: bool = False,
                       override: bool = False, preserve_ram: bool = True):
    partitions, merged = get_globs(snapshot_dir, last_update, 'publisher')
    logging.info(f'Looks like there are {len(partitions):,} publisher partitions '
                 f'and {len(merged):,} merged_ids partitions since last update ({last_update}).')
    run(flatten_publishers_partition_kw, [
        {
            'partition': partition,
            'out_sql_cpy': tmp_dir / f'pg-publisher-{name_part(partition)}-cpy.sql',
            'out_sql_del': tmp_dir / f'pg-publisher-{name_part(partition)}-del.sql',
            'out_publishers': tmp_dir / f'pg-publisher-{name_part(partition)}_publishers.csv.gz',
            'preserve_ram': preserve_ram,
            'pg_schema': pg_schema
        }
        for partition in partitions
    ], parallelism=parallelism, override=override)

    if not skip_deletion:
        generate_deletions_from_merge_file(merge_files=merged,
                                           out_file=tmp_dir / f'pg-publisher-{last_update}-merged_del.sql',
                                           object_type='publisher',
                                           pg_schema=pg_schema,
                                           batch_size=1000)


def flatten_funders(tmp_dir: Path, snapshot_dir: Path, last_update: str, pg_schema: str, parallelism: int = 8,
                    skip_deletion: bool = False,
                    override: bool = False, preserve_ram: bool = True):
    partitions, merged = get_globs(snapshot_dir, last_update, 'funder')
    logging.info(f'Looks like there are {len(partitions):,} funder partitions '
                 f'and {len(merged):,} merged_ids partitions since last update ({last_update}).')
    run(flatten_funders_partition_kw,
        [
            {
                'partition': partition,
                'out_sql_cpy': tmp_dir / f'pg-funder-{name_part(partition)}-cpy.sql',
                'out_sql_del': tmp_dir / f'pg-funder-{name_part(partition)}-del.sql',
                'out_funders': tmp_dir / f'pg-funder-{name_part(partition)}_funders.csv.gz',
                'preserve_ram': preserve_ram,
                'pg_schema': pg_schema
            }
            for partition in partitions
        ], parallelism=parallelism, override=override)

    if not skip_deletion:
        generate_deletions_from_merge_file(merge_files=merged,
                                           out_file=tmp_dir / f'pg-funder-{last_update}-merged_del.sql',
                                           object_type='funder',
                                           pg_schema=pg_schema,
                                           batch_size=1000)


def flatten_concepts(tmp_dir: Path, snapshot_dir: Path, last_update: str, pg_schema: str, parallelism: int = 8,
                     skip_deletion: bool = False,
                     override: bool = False, preserve_ram: bool = True):
    partitions, merged = get_globs(snapshot_dir, last_update, 'concept')
    logging.info(f'Looks like there are {len(partitions):,} concepts partitions '
                 f'and {len(merged):,} merged_ids partitions since last update ({last_update}).')
    run(flatten_concepts_partition_kw,
        [
            {
                'partition': partition,
                'out_sql_cpy': tmp_dir / f'pg-concept-{name_part(partition)}-cpy.sql',
                'out_sql_del': tmp_dir / f'pg-concept-{name_part(partition)}-del.sql',
                'out_concepts': tmp_dir / f'pg-concept-{name_part(partition)}_concepts.csv.gz',
                'out_m2m_ancestor': tmp_dir / f'pg-concept-{name_part(partition)}_concepts_ancestor.csv.gz',
                'out_m2m_related': tmp_dir / f'pg-concept-{name_part(partition)}_concepts_related.csv.gz',
                'preserve_ram': preserve_ram,
                'pg_schema': pg_schema
            }
            for partition in partitions
        ], parallelism=parallelism, override=override)

    if not skip_deletion:
        generate_deletions_from_merge_file(merge_files=merged,
                                           out_file=tmp_dir / f'pg-concept-{last_update}-merged_del.sql',
                                           object_type='concept',
                                           pg_schema=pg_schema,
                                           batch_size=1000)


def flatten_topics(tmp_dir: Path, snapshot_dir: Path, last_update: str, pg_schema: str, parallelism: int = 8,
                   skip_deletion: bool = False,
                   override: bool = False, preserve_ram: bool = True):
    partitions, merged = get_globs(snapshot_dir, last_update, 'topic')
    logging.info(f'Looks like there are {len(partitions):,} topic partitions '
                 f'and {len(merged):,} merged_ids partitions since last update ({last_update}).')
    run(flatten_topics_partition_kw,
        [
            {
                'partition': partition,
                'out_sql_cpy': tmp_dir / f'pg-concept-{name_part(partition)}-cpy.sql',
                'out_topics': tmp_dir / f'pg-topic-{name_part(partition)}_topics.csv.gz',
                'preserve_ram': preserve_ram,
                'pg_schema': pg_schema
            }
            for partition in partitions
        ], parallelism=parallelism, override=override)


def flatten_subfields(tmp_dir: Path, snapshot_dir: Path, last_update: str, pg_schema: str, parallelism: int = 8,
                      skip_deletion: bool = False,
                      override: bool = False, preserve_ram: bool = True):
    partitions, merged = get_globs(snapshot_dir, last_update, 'subfield')
    logging.info(f'Looks like there are {len(partitions):,} subfield partitions '
                 f'and {len(merged):,} merged_ids partitions since last update ({last_update}).')
    run(flatten_subfields_partition_kw,
        [
            {
                'partition': partition,
                'out_sql_cpy': tmp_dir / f'pg-concept-{name_part(partition)}-cpy.sql',
                'out_subfields': tmp_dir / f'pg-subfield-{name_part(partition)}_subfields.csv.gz',
                'preserve_ram': preserve_ram,
                'pg_schema': pg_schema
            }
            for partition in partitions
        ], parallelism=parallelism, override=override)


def flatten_fields(tmp_dir: Path, snapshot_dir: Path, last_update: str, pg_schema: str, parallelism: int = 8,
                   skip_deletion: bool = False,
                   override: bool = False, preserve_ram: bool = True):
    partitions, merged = get_globs(snapshot_dir, last_update, 'field')
    logging.info(f'Looks like there are {len(partitions):,} field partitions '
                 f'and {len(merged):,} merged_ids partitions since last update ({last_update}).')
    run(flatten_fields_partition_kw,
        [
            {
                'partition': partition,
                'out_sql_cpy': tmp_dir / f'pg-concept-{name_part(partition)}-cpy.sql',
                'out_fields': tmp_dir / f'pg-field-{name_part(partition)}_fields.csv.gz',
                'preserve_ram': preserve_ram,
                'pg_schema': pg_schema
            }
            for partition in partitions
        ], parallelism=parallelism, override=override)


def flatten_domains(tmp_dir: Path, snapshot_dir: Path, last_update: str, pg_schema: str, parallelism: int = 8,
                    skip_deletion: bool = False,
                    override: bool = False, preserve_ram: bool = True):
    partitions, merged = get_globs(snapshot_dir, last_update, 'domain')
    logging.info(f'Looks like there are {len(partitions):,} domain partitions '
                 f'and {len(merged):,} merged_ids partitions since last update ({last_update}).')
    run(flatten_domains_partition_kw,
        [
            {
                'partition': partition,
                'out_sql_cpy': tmp_dir / f'pg-concept-{name_part(partition)}-cpy.sql',
                'out_domains': tmp_dir / f'pg-domain-{name_part(partition)}_domains.csv.gz',
                'preserve_ram': preserve_ram,
                'pg_schema': pg_schema
            }
            for partition in partitions
        ], parallelism=parallelism, override=override)


def flatten_sources(tmp_dir: Path, snapshot_dir: Path, last_update: str, pg_schema: str, parallelism: int = 8,
                    skip_deletion: bool = False,
                    override: bool = False, preserve_ram: bool = True):
    partitions, merged = get_globs(snapshot_dir, last_update, 'source')
    logging.info(f'Looks like there are {len(partitions):,} source partitions '
                 f'and {len(merged):,} merged_ids partitions since last update ({last_update}).')
    run(flatten_sources_partition_kw,
        [
            {
                'partition': partition,
                'out_sql_cpy': tmp_dir / f'pg-source-{name_part(partition)}-cpy.sql',
                'out_sql_del': tmp_dir / f'pg-source-{name_part(partition)}-del.sql',
                'out_sources': tmp_dir / f'pg-source-{name_part(partition)}_sources.csv.gz',
                'preserve_ram': preserve_ram,
                'pg_schema': pg_schema
            }
            for partition in partitions
        ], parallelism=parallelism, override=override)

    if not skip_deletion:
        generate_deletions_from_merge_file(merge_files=merged,
                                           out_file=tmp_dir / f'pg-source-{last_update}-merged_del.sql',
                                           object_type='source',
                                           pg_schema=pg_schema,
                                           batch_size=1000)


def flatten_works(tmp_dir: Path, snapshot_dir: Path, last_update: str, pg_schema: str, parallelism: int = 8,
                  skip_deletion: bool = False,
                  override: bool = False, preserve_ram: bool = True):
    partitions, merged = get_globs(snapshot_dir, last_update, 'work')
    logging.info(f'Looks like there are {len(partitions):,} works partitions '
                 f'and {len(merged):,} merged_ids partitions since last update ({last_update}).')
    run(flatten_works_partition_kw,
        [
            {
                'partition': partition,
                'out_sql_cpy': tmp_dir / f'pg-work-{name_part(partition)}-cpy.sql',
                'out_sql_del': tmp_dir / f'pg-work-{name_part(partition)}-del.sql',
                'out_works': tmp_dir / f'pg-work-{name_part(partition)}_works.csv.gz',
                'out_m2m_locations': tmp_dir / f'pg-work-{name_part(partition)}_works_locations.csv.gz',
                'out_m2m_concepts': tmp_dir / f'pg-work-{name_part(partition)}_works_concepts.csv.gz',
                'out_m2m_authorships': tmp_dir / f'pg-work-{name_part(partition)}_works_authorships.csv.gz',
                'out_m2m_authorship_institutions': tmp_dir / f'pg-work-{name_part(partition)}_works_authorship_institutions.csv.gz',
                'out_m2m_references': tmp_dir / f'pg-work-{name_part(partition)}_works_references.csv.gz',
                'out_m2m_related': tmp_dir / f'pg-work-{name_part(partition)}_works_related.csv.gz',
                'out_m2m_sdgs': tmp_dir / f'pg-work-{name_part(partition)}_works_sdgs.csv.gz',
                'out_m2m_topics': tmp_dir / f'pg-work-{name_part(partition)}_works_topics.csv.gz',
                'preserve_ram': preserve_ram,
                'pg_schema': pg_schema
            }
            for partition in partitions
        ], parallelism=parallelism, override=override)

    if not skip_deletion:
        generate_deletions_from_merge_file(merge_files=merged,
                                           out_file=tmp_dir / f'pg-work-{last_update}-merged_del.sql',
                                           object_type='work',
                                           pg_schema=pg_schema,
                                           batch_size=1000)
