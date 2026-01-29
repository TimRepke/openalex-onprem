from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated

import httpx
import typer

from nacsos_data.models.openalex import WorksSchema
from nacsos_data.util.academic.apis.openalex import OpenAlexAPI
from nacsos_data.util import batched

from shared.crud import queue_requests
from shared.db import get_engine
from shared.schema import Queue
from shared.util import get_logger
from shared.config import load_settings

app = typer.Typer()


@app.command('day')
def load_updated_records_from_api(
    config: Annotated[Path, typer.Option(help='Path to config file')],
    date: Annotated[datetime, typer.Option(help='Get works created or updated on this day')],
    solr_buffer_size: int = 200,
    loglevel: str = 'INFO',
):
    logger = get_logger('openalex-ingest', loglevel=loglevel)

    logger.info(f'Loading config from {config.resolve()}...')
    if not config.exists():
        raise AssertionError(f'Config file does not exist at {config.resolve()}!')
    settings = load_settings(config)

    logger.info('Connecting to database...')
    db_engine = get_engine(settings=settings.CACHE_DB)

    logger.info(f'Will use solr collection at: {settings.OPENALEX.solr_url}')

    for fltr in ['created', 'updated']:
        for batch in batched(
            OpenAlexAPI(
                api_key=settings.OPENALEX.API_KEY,
                logger=logger,
            ).fetch_raw(
                query='',
                params={
                    'filter': f'from_{fltr}_date:{date.strftime("%Y-%m-%d")},to_{fltr}_date:{date.strftime("%Y-%m-%d")},',
                    'include_xpac': 'true',
                },
            ),
            batch_size=solr_buffer_size,
        ):
            res: httpx.Response | None = None
            try:
                works = [WorksSchema.model_validate(record) for record in batch]
                logger.debug(f'Got {len(works):,} works entries from API for "{fltr}", POSTing to solr...')
                res = httpx.post(
                    url=f'{settings.OPENALEX.solr_url}/update/json?commit=true',
                    timeout=240,
                    headers={'Content-Type': 'application/json'},
                    data='\n'.join([w.model_dump_json() for w in works]),
                )

                # remember all Works without abstract and with DOI
                queue = [Queue(doi=w.doi, openalex_id=w.id) for w in works if w.id is not None and w.doi is not None and w.abstract is None]
                queue_requests(db_engine=db_engine, entries=queue)

                logger.debug(f'Wrote {len(queue):,} entries to into the meta-cache queue')

            except httpx.HTTPError as e:
                if res:
                    logger.error(res.text)
                logger.error(f'Failed to submit: {e}')
                logger.exception(e)

    logger.info('Solr collection is up to date.')


@app.command('bulk')
def bulk_api_pull(
    config: Annotated[Path, typer.Option(help='Path to config file')],
    from_date: Annotated[datetime, typer.Option(help='First day to start pulling updates from')],
    to_date: Annotated[datetime, typer.Option(help='Last day to include updates from')],
    solr_buffer_size: int = 200,
    loglevel: str = 'INFO',
):
    logger = get_logger('BULK', loglevel=loglevel)
    if from_date > to_date:
        raise AssertionError('from_date must be before to_date')
    delta = (to_date - from_date).days
    logger.info(f'Pulling {delta} days from {from_date} to {to_date}...')

    date = from_date
    for day in range(delta):
        logger.info(f'Pulling data for day {day + 1}/{delta} ({date})')
        load_updated_records_from_api(
            config=config,
            date=date,
            solr_buffer_size=solr_buffer_size,
            loglevel=loglevel,
        )
        date = date + timedelta(days=1)


def main():
    app()


if __name__ == '__main__':
    main()
