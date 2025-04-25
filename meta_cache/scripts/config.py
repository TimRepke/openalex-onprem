import logging.config
import os
import toml
from pydantic import PostgresDsn, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from meta_cache.handlers.db import DatabaseEngine


class Settings(BaseSettings):
    LOG_CONFIG_FILE: str = 'config/logging.toml'
    DEBUG_MODE: bool = False  # set this to true in order to get more detailed logs

    DB_SCHEME: str = 'postgresql'
    DB_SCHEMA: str = 'public'
    DB_HOST: str = 'localhost'  # host of the db server
    DB_PORT: int = 5432  # port of the db server
    DB_USER: str = 'meta_cache'  # username for the database
    DB_PASSWORD: str = 'secr€t_passvvord'  # password for the database user
    DB_DATABASE: str = 'meta_cache'  # name of the database

    NACSOS_HOST: str = "127.0.0.1"
    NACSOS_PORT: int = 5432
    NACSOS_USER: str = "user"
    NACSOS_PASSWORD: str = "secret"
    NACSOS_DATABASE: str = "db"

    OA_SOLR_HOST: str = 'http://localhost:8983'
    OA_SOLR_COLLECTION: str = 'openalex'

    @property
    def cache_db(self):
        return PostgresDsn.build(
            scheme=getattr(self, 'DB_SCHEME', 'postgresql'),
            username=getattr(self, 'DB_USER'),
            password=getattr(self, 'DB_PASSWORD'),
            host=getattr(self, 'DB_HOST'),
            port=getattr(self, 'DB_PORT'),
            path=f'/{getattr(self, "DB_DATABASE", "")}',
        )

    @property
    def nacsos_db(self):
        return PostgresDsn.build(
            scheme=getattr(self, 'DB_SCHEME', 'postgresql'),
            username=getattr(self, 'NACSOS_USER'),
            password=getattr(self, 'NACSOS_PASSWORD'),
            host=getattr(self, 'NACSOS_HOST'),
            port=getattr(self, 'NACSOS_PORT'),
            path=f'/{getattr(self, "NACSOS_DATABASE", "")}',
        )

    model_config = SettingsConfigDict(case_sensitive=True, env_prefix='OACACHE_', extra='allow')


conf_file = os.environ.get('OACACHE_CONFIG', 'config/scripts.env')
settings = Settings(_env_file=conf_file, _env_file_encoding='utf-8')  # type: ignore[call-arg]

with open(settings.LOG_CONFIG_FILE, 'r') as f:
    ret = toml.loads(f.read())
    logging.config.dictConfig(ret)

db_engine_cache = DatabaseEngine(host=settings.DB_HOST,
                                 port=settings.DB_PORT,
                                 user=settings.DB_USER,
                                 password=settings.DB_PASSWORD,
                                 database=settings.DB_DATABASE,
                                 debug=settings.DEBUG_MODE)
db_engine_nacsos = DatabaseEngine(host=settings.NACSOS_HOST,
                                  port=settings.NACSOS_PORT,
                                  user=settings.NACSOS_USER,
                                  password=settings.NACSOS_PASSWORD,
                                  database=settings.NACSOS_DATABASE,
                                  debug=settings.DEBUG_MODE)

db_engine_cache.startup()

__all__ = ['settings', 'conf_file', 'db_engine_cache', 'db_engine_nacsos']
