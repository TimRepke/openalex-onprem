from pathlib import Path
from typing import Annotated
from datetime import datetime
from itertools import batched

import typer
from nacsos_data.util.academic.apis import APIEnum

from openalex_ingest.shared.models import SourcePriority
from openalex_ingest.shared.schema import Queue
from openalex_ingest.shared.solr import check_openalex_ids
from openalex_ingest.shared.util import prepare_runner


def main(
    source: Annotated[Path, typer.Option(help='Path to file with OpenAlex IDs (stripped, one id per line')],
    config: Annotated[Path, typer.Option(help='Path to config file')],
    sources: Annotated[list[str] | None, typer.Option(help='Sources to include')] = None,
    batch_size: Annotated[int, typer.Option(help='Batch size for processing')] = 5000,
    loglevel: Annotated[str, typer.Option(help='Path to config file')] = 'INFO',
):
    logger, settings, db_engine = prepare_runner(config=config, loglevel=loglevel, logger_name='openalex-backup', run_log_init=True)
    start_time = datetime.now()

    if sources is None or len(sources) == 0:
        sources_ = [APIEnum.DIMENSIONS, APIEnum.SCOPUS, APIEnum.PUBMED, APIEnum.WOS]
    else:
        sources_ = [getattr(APIEnum, source) for source in sources]

    n_checked = 0
    n_missing_abstract = 0
    n_queued = 0
    with open(source) as f_in, db_engine.session() as session:
        for lines in batched(f_in, batch_size):
            ids = [line.strip() for line in lines]
            missing_abstract_ids = check_openalex_ids(config=settings.OPENALEX, check_abstract=True, reference_ids=ids, return_fields='id,doi')
            queue_entries = [
                Queue(
                    openalex_id=entry['id'],
                    doi=entry['doi'],
                    sources=[(src, SourcePriority.TRY) for src in sources_],
                )
                for entry in missing_abstract_ids
                if entry.get('doi') is not None
            ]
            session.add_all(queue_entries)
            session.flush()

            n_checked += len(ids)
            n_missing_abstract += len(missing_abstract_ids)
            n_queued += len(queue_entries)

            logger.debug(
                f'Checked {len(ids):,} IDs of which {len(missing_abstract_ids):,} had no abstract of which {len(queue_entries):,} had a DOI // '
                f'Cumulative counts: {n_checked:,} checked, {n_missing_abstract:,} missing abstracts, {n_queued:,} queued',
            )

        session.commit()

    src_options = [f'--sources={src.value}' for src in sources_]
    end_time = datetime.now()

    logger.info('All done, now run')
    logger.info(
        f'  uv run openalex_ingest queue-worker --config={config} --max-runtime={n_queued * 2} --batch-size=25  {" ".join(src_options)}'
        f' --loglevel={loglevel} --min-abstract-len=25'
        f' --created-after={start_time.strftime("%Y-%m-%dT%H:%M:%S")}'
        f' --created-before={end_time.strftime("%Y-%m-%dT%H:%M:%S")}',
    )


if __name__ == '__main__':
    typer.run(main)
