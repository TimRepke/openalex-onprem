import re
import logging
from contextlib import ContextDecorator
from pathlib import Path
from time import perf_counter, sleep
from typing import TypeVar, Iterable

import typer

from shared.config import load_settings, Settings
from shared.db import get_engine, DatabaseEngine

logger = logging.getLogger('openalex.shared.util')

T = TypeVar('T')


def date_check(value: str | None) -> str | None:
    if value is None:
        return value
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
        raise typer.BadParameter(f'Invalid date format, not seeing YYYY-MM-DD instead got  {value}')
    return value


def it_limit(iterable: Iterable[T], limit: int | None = None) -> Iterable[T]:
    for i, item in enumerate(iterable):
        if limit is not None and i >= limit:
            break
        yield item


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


def get_logger(logger_name: str, run_log_init=True, loglevel: str = 'INFO') -> logging.Logger:
    if run_log_init:
        logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s (%(process)d): %(message)s', level=loglevel)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('root').setLevel(loglevel)

    logger = logging.getLogger(logger_name)
    logger.setLevel(loglevel)
    return logger


def prepare_runner(config: Path, logger_name: str, run_log_init=True, loglevel: str = 'INFO') -> tuple[logging.Logger, Settings, DatabaseEngine]:
    logger = get_logger(logger_name=logger_name, run_log_init=run_log_init, loglevel=loglevel)

    logger.info(f'Loading config from {config.resolve()}...')
    if not config.exists():
        raise AssertionError(f'Config file does not exist at {config.resolve()}!')
    settings = load_settings(config)

    logger.info('Connecting to database...')
    db_engine = get_engine(settings=settings.CACHE_DB)
    return logger, settings, db_engine
