"""
Sometimes, DOIs are not pulled from the meta-data correctly and the match to the OpenAlex ID fails.
This script is to help resolve those issues as best as possible.
It assumes, that the DOIs are now fixed in the request table and just need to be matched to the OpenAlex ID.
It also assumes, that you have a file with all OpenAlex IDs that you are expecting to find,because a DOI might occur multiple times in OpenAlex,
and we need to identify the correct work object.

First, triple-check why DOIs might be missing and adapt the following UPDATE queries:
        UPDATE request SET doi = jsonb_path_query_first(raw,
            '$.PubmedData[*].ArticleIdList[*].ArticleId[*] ? (@."@IdType" == "doi")._text'
          )#>>'{}'
        WHERE doi IS NULL AND wrapper='PUBMED' AND jsonb_path_query_first(raw,
            '$.PubmedData[*].ArticleIdList[*].ArticleId[*] ? (@."@IdType" == "doi")._text'
          )#>>'{}' IS NOT NULL;

        UPDATE request SET doi = jsonb_path_query_first(
            raw,
            '$.dynamic_data.cluster_related.identifiers.identifier[*] ? (@.type == "xref_doi" || @.type == "doi").value'
          )#>>'{}'
        WHERE doi IS NULL AND wrapper='WOS' AND jsonb_path_query_first(
            raw,
            '$.dynamic_data.cluster_related.identifiers.identifier[*] ? (@.type == "xref_doi" || @.type == "doi").value'
          )#>>'{}' IS NOT NULL;
"""

from pathlib import Path
from typing import Annotated
from collections import defaultdict
import httpx
import typer
import sqlalchemy as sa

from nacsos_data.models.openalex import strip_url
from tqdm import tqdm

from openalex_ingest.shared.util import prepare_runner


def main(
    reference_ids: Annotated[Path, typer.Option(help='Path to file with OpenAlex IDs (stripped, one id per line')],
    config: Annotated[Path, typer.Option(help='Path to config file')],
    batch_size: Annotated[int, typer.Option(help='Batch size for processing')] = 20,
    loglevel: Annotated[str, typer.Option(help='Path to config file')] = 'INFO',
):
    logger, settings, db_engine = prepare_runner(config=config, loglevel=loglevel, logger_name='openalex-backup', run_log_init=True, db_debug=False)

    with open(reference_ids) as f_in:
        openalex_ids = {line.strip() for line in f_in}
    logger.info(f'Found {len(openalex_ids):,} OpenAlex IDs for reference; small sample: {list(openalex_ids)[:10]}')

    n_tested = 0
    n_results = 0
    n_matched = 0
    with db_engine.session() as session, db_engine.session() as write_session:
        count = session.execute(sa.text('SELECT count(1) FROM request WHERE doi IS NOT NULL AND openalex_id IS NULL;')).scalar()
        logger.info(f'Found {count:,} records that need fixing')
        progress = tqdm(total=count)

        partitions = (
            session.execute(
                sa.text(
                    'SELECT record_id, openalex_id, doi FROM request WHERE doi IS NOT NULL AND openalex_id IS NULL ORDER BY time_created desc;',
                ),
                execution_options={'yield_per': batch_size},
            )
            .mappings()
            .partitions(batch_size)
        )

        for partition in partitions:
            logger.debug(f'Processing batch of {len(partition):,} rows from `request` table')
            records = defaultdict(list)
            for record in partition:
                records[record['doi'].lower()].append(record['record_id'])

            n_tested += len(records)
            if len(records) == 0:
                continue
            try:
                dois_ = [f'https://doi.org/{doi}' for doi in records.keys()]
                response = httpx.get(f'https://api.openalex.org/works?select=id,doi&filter=doi:{"|".join(dois_)}').json()
                results = response.get('results', [])
                logger.debug(f'Received {len(results):,} results from OpenAlex API for {len(dois_):,} DOIs')
                if len(results) == 0:
                    continue
                n_results += len(results)

                n_matched_ = 0
                for work in results:
                    openalex_id = strip_url(work['id']).upper()

                    if openalex_id not in openalex_ids:
                        continue

                    doi = strip_url(work['doi']).lower()
                    if doi not in records:
                        continue

                    n_matched += 1
                    n_matched_ += 1
                    logger.debug(f'Updating ({doi}, {openalex_id}) for {records[doi]})')
                    write_session.execute(
                        sa.text('UPDATE request SET openalex_id = :openalex_id WHERE record_id = ANY(:record_ids)'),
                        {'record_ids': records[doi], 'openalex_id': openalex_id},
                    )
                write_session.commit()
                logger.debug(f'Updated rows for {n_matched_:,} DOI matches')

            except Exception as e:
                logger.error(f'Failed to get results from `request` table: {e}')
                logger.exception(e)
            progress.set_postfix_str(
                f'tested={n_tested:,}, found={n_results:,}, matched={n_matched:,} ',
            )
            progress.update(len(partition))

    logger.info(
        f'Finished with tested={n_tested:,}, found={n_results:,}, matched={n_matched:,} ',
    )


if __name__ == '__main__':
    typer.run(main)
