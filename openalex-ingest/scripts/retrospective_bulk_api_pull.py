import logging
from pathlib import Path
from typing import Annotated
from datetime import datetime, timedelta
import httpx
import typer

from daily.pull_api_update import load_updated_records_from_api
from shared.util import date_check, get_logger


def bulk_api_pull(
    config: Annotated[Path, typer.Option(help='Path to config file')],
    from_date: Annotated[str, typer.Option(callback=date_check, help='First day to start pulling updates from')],
    to_date: Annotated[str, typer.Option(callback=date_check, help='Last day to include updates from')],
    solr_buffer_size: int = 200,
    loglevel: str = 'INFO',
):
    logger = get_logger('OA-API', loglevel='DEBUG')
    day = timedelta(days=1)

    pass


def main():
    typer.run(bulk_api_pull)


if __name__ == '__main__':
    main()
