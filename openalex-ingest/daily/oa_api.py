import logging
from pathlib import Path
from typing import Annotated
import httpx
import typer
from nacsos_data.models.openalex import WorksSchema
from nacsos_data.util.academic.apis.openalex import OpenAlexAPI
from nacsos_data.util.conf import load_settings
from nacsos_data.util import batched

from .util import date_check


def update_solr(
        config: Annotated[Path, typer.Option(help='OpenAlex premium API key')],
        date: Annotated[str, typer.Option(callback=date_check, help='Get works created or updated on this day')],
        solr_buffer_size: int = 200,
        loglevel: str = 'INFO',
):
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s (%(process)d): %(message)s', level=loglevel)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('root').setLevel(loglevel)

    logger = logging.getLogger('openalex-ingest')
    logger.setLevel(loglevel)

    logger.info(f'Loading config from {config.resolve()}...')
    if not config.exists():
        raise AssertionError(f'Config file does not exist at {config.resolve()}!')
    config = load_settings(config)
    logger.info(f'Will use solr collection at: {config.OPENALEX.solr_url}')

    for fltr in ['created','updated']:
        for batch in batched(
                OpenAlexAPI(
                    api_key=config.OPENALEX.API_KEY,
                    logger=logger,
                ).fetch_raw(
                    query='',
                    params={
                        'filter': f'from_{fltr}_date:{date},'
                                  f'to_{fltr}_date:{date},',
                        'include_xpac': 'true',
                    },
                ),
                batch_size=solr_buffer_size,
        ):
            try:
                res = httpx.post(
                    url=f'{config.OPENALEX.solr_url}/update/json?commit=true',
                    timeout=240,
                    headers={'Content-Type': 'application/json'},
                    data='\n'.join([WorksSchema.model_validate(record).model_dump_json() for record in batch]),
                )
                res.raise_for_status()
            except httpx.HTTPError as e:
                logging.error(f'Failed to submit: {e}')
                logging.exception(e)

    logging.info('Solr collection is up to date.')
