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
from nacsos_data.util.conf import DatabaseConfig

from .config import load_settings

# unused import required so the engine sees the models!
from . import schema  # noqa F401

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

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str = 'meta_cache',
        debug: bool = False,
    ):
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._database = database

        self._connection_str = URL.create(
            drivername='postgresql+psycopg2',
            username=self._user,
            password=self._password,
            host=self._host,
            port=self._port,
            database=self._database,
        )

        self.engine = create_engine(
            self._connection_str,
            echo=debug,
            future=True,
            json_serializer=DictLikeEncoder().encode,
        )

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


def get_engine(
    conf_file: str | None = None,
    settings: DatabaseConfig | None = None,
    use_nacsos: bool = False,
    debug: bool = False,
) -> DatabaseEngine:
    if settings is None:
        if conf_file is None:
            raise AssertionError('Neither `settings` not `conf_file` specified.')
        _settings = load_settings(conf_file=conf_file)
        if use_nacsos:
            settings = _settings.DB
        else:
            settings = _settings.CACHE_DB

    return DatabaseEngine(
        host=settings.HOST,
        port=settings.PORT,
        user=settings.USER,
        password=settings.PASSWORD,
        database=settings.DATABASE,
        debug=debug,
    )
