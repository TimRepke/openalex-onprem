import os
import json
import logging
from pathlib import Path
from typing import Iterator, Any
from json import JSONEncoder

from pydantic import BaseModel
from sqlalchemy import URL
from contextlib import contextmanager
from datetime import datetime
from sqlmodel import create_engine, Session, SQLModel

# unused import required so the engine sees the models!
from . import schema  # noqa F401
from .. import setup as config

logger = logging.getLogger('nacsos_data.engine')


class DictLikeEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        # Translate datetime into a string
        if isinstance(o, datetime):
            return o.strftime('%Y-%m-%dT%H:%M:%S')

        # Translate Path into a string
        if isinstance(o, Path):
            return str(o)

        # Translate pydantic models into dict
        if isinstance(o, BaseModel):
            return o.model_dump()

        return json.JSONEncoder.default(self, o)


class DatabaseEngine:
    """
    This class is the main entry point to access the database.
    It handles the connection, engine, and session.
    """

    def __init__(self, host: str, port: int, user: str, password: str,
                 database: str = 'nacsos_core', debug: bool = False):
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._database = database

        self._connection_str = URL.create(
            drivername='postgresql+psycopg',
            username=self._user,
            password=self._password,
            host=self._host,
            port=self._port,
            database=self._database,
        )

        self.engine = create_engine(self._connection_str, echo=debug, future=True,
                                    json_serializer=DictLikeEncoder().encode)

    def startup(self) -> None:
        """
        Call this function to initialise the database engine.
        """
        SQLModel.metadata.create_all(self.engine)

    def __call__(self, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Session:
        return Session(self.engine)

    @contextmanager
    def session(self) -> Iterator[Session]:
        # https://rednafi.github.io/digressions/python/2020/03/26/python-contextmanager.html
        session = Session(self.engine)
        try:
            yield session
            # session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


def _get_settings(conf_file: str | None = None) -> config.Settings:
    if conf_file is None:
        conf_file = os.environ.get('OACACHE_CONFIG', 'config/default.env')
    if not Path(conf_file).is_file():
        raise FileNotFoundError(f'Configuration file not found: {conf_file}')
    return config.Settings(_env_file=conf_file, _env_file_encoding='utf-8')  # type: ignore[call-arg]


def get_engine(conf_file: str | None = None,
               settings: config.Settings | None = None,
               debug: bool = False) -> DatabaseEngine:
    if settings is None:
        if conf_file is None:
            raise AssertionError('Neither `settings` not `conf_file` specified.')
        settings = _get_settings(conf_file)

    return DatabaseEngine(host=settings.DB_HOST, port=settings.DB_PORT,
                          user=settings.DB_USER, password=settings.DB_PASSWORD,
                          database=settings.DB_DATABASE, debug=debug)
