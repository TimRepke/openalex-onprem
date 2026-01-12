import logging
import re
from contextlib import ContextDecorator
from time import perf_counter, sleep

import typer


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


def date_check(value: str | None) -> str | None:
    if value is None:
        return value
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
        raise typer.BadParameter(f'Invalid date format, not seeing YYYY-MM-DD instead got  {value}')
    return value
