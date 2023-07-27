import csv
import gzip
import logging
from pathlib import Path

from msgspec.json import Decoder

import structs
from deletion import generate_deletions
from shared.config import settings


def flatten_authors_partition(partition: Path,
                              out_sql_cpy: Path,
                              out_sql_del: Path,
                              out_authors: Path,
                              out_m2m_institution: Path):
    logging.info(f'Flattening partition file {partition}')
    with (gzip.open(out_authors, 'wt', encoding='utf-8') as f_authors,
          gzip.open(out_m2m_institution, 'wt', encoding='utf-8') as f_m2m,
          open(out_sql_del, 'w') as f_sql_del,
          open(out_sql_cpy, 'w') as f_sql_cpy,
          gzip.open(partition, 'rb') as f_in):
        writer_authors = csv.DictWriter(f_authors,
                                        fieldnames=['id',
                                                    'cited_by_count', 'works_count', 'h_index', 'i10_index',
                                                    'display_name', 'display_name_alternatives',
                                                    'id_mag', 'id_orcid', 'id_scopus', 'id_twitter', 'id_wiki',
                                                    'created_date', 'updated_date'],
                                        extrasaction='ignore')
        writer_authors.writeheader()
        writer_m2m = csv.DictWriter(f_m2m, fieldnames=['author_id', 'institution_id'], extrasaction='ignore')
        writer_m2m.writeheader()

        decoder = Decoder(structs.Author)

        n_authors = 0
        author_ids = []

        for line in f_in:
            n_authors += 1
            author = decoder.decode(line)
            aid = author.id[21:]
            author_ids.append(aid)

            alt_names = None
            if author.display_name_alternatives is not None and len(author.display_name_alternatives) > 0:
                alt_names = ','.join([an.replace(',', '') for an in author.display_name_alternatives])

            writer_authors.writerow({
                'id': aid,
                'cited_by_count': author.cited_by_count,
                'works_count': author.works_count,
                'h_index': author.summary_stats.h_index,
                'i10_index': author.summary_stats.i10_index,
                'display_name': author.display_name,
                'display_name_alternatives': '{' + alt_names + '}' if alt_names is not None else None,
                'id_mag': author.ids.mag,
                'id_orcid': author.ids.orcid,
                'id_scopus': author.ids.scopus,
                'id_twitter': author.ids.twitter,
                'id_wiki': author.ids.wikipedia,
                'created_date': author.created_date,
                'updated_date': author.updated_date
            })

            for institution in author.last_known_institution:
                writer_m2m.writerow({
                    'author_id': aid,
                    'institution_id': institution.id[21:]
                })

        for del_row in generate_deletions(ids=author_ids, object_type='author', batch_size=1000):
            f_sql_del.write(del_row + '\n')

        f_sql_cpy.write(f"COPY {settings.pg_schema}.authors "
                        f"FROM PROGRAM 'gunzip -c {out_authors.absolute()}' csv header;\n\n")
        f_sql_cpy.write(f"COPY {settings.pg_schema}.authors_institutions "
                        f"FROM PROGRAM 'gunzip -c {out_m2m_institution.absolute()}' csv header;\n\n")


def flatten_institutions_partition(partition: Path,
                                   out_sql_cpy: Path,
                                   out_sql_del: Path,
                                   out_institutions: Path,
                                   out_m2m_institution: Path):
    logging.info(f'Flattening partition file {partition}')
    with (gzip.open(out_authors, 'wt', encoding='utf-8') as f_authors,
          gzip.open(out_m2m_institution, 'wt', encoding='utf-8') as f_m2m,
          open(out_sql_del, 'w') as f_sql_del,
          open(out_sql_cpy, 'w') as f_sql_cpy,
          gzip.open(partition, 'rb') as f_in):
        writer_authors = csv.DictWriter(f_authors,
                                        fieldnames=['id',
                                                    'cited_by_count', 'works_count', 'h_index', 'i10_index',
                                                    'display_name', 'display_name_alternatives',
                                                    'id_mag', 'id_orcid', 'id_scopus', 'id_twitter', 'id_wiki',
                                                    'created_date', 'updated_date'],
                                        extrasaction='ignore')
        writer_authors.writeheader()
        writer_m2m = csv.DictWriter(f_m2m, fieldnames=['author_id', 'institution_id'], extrasaction='ignore')
        writer_m2m.writeheader()

        decoder = Decoder(structs.Author)

        n_authors = 0
        author_ids = []

        for line in f_in:
            n_authors += 1
            author = decoder.decode(line)
            aid = author.id[21:]
            author_ids.append(aid)

            alt_names = None
            if author.display_name_alternatives is not None and len(author.display_name_alternatives) > 0:
                alt_names = ','.join([an.replace(',', '') for an in author.display_name_alternatives])

            writer_authors.writerow({
                'id': aid,
                'cited_by_count': author.cited_by_count,
                'works_count': author.works_count,
                'h_index': author.summary_stats.h_index,
                'i10_index': author.summary_stats.i10_index,
                'display_name': author.display_name,
                'display_name_alternatives': '{' + alt_names + '}' if alt_names is not None else None,
                'id_mag': author.ids.mag,
                'id_orcid': author.ids.orcid,
                'id_scopus': author.ids.scopus,
                'id_twitter': author.ids.twitter,
                'id_wiki': author.ids.wikipedia,
                'created_date': author.created_date,
                'updated_date': author.updated_date
            })

            for institution in author.last_known_institution:
                writer_m2m.writerow({
                    'author_id': aid,
                    'institution_id': institution.id[21:]
                })

        for del_row in generate_deletions(ids=author_ids, object_type='author', batch_size=1000):
            f_sql_del.write(del_row + '\n')

        f_sql_cpy.write(f"COPY {settings.pg_schema}.authors "
                        f"FROM PROGRAM 'gunzip -c {out_authors.absolute()}' csv header;\n\n")
        f_sql_cpy.write(f"COPY {settings.pg_schema}.authors_institutions "
                        f"FROM PROGRAM 'gunzip -c {out_m2m_institution.absolute()}' csv header;\n\n")
