import os
from pathlib import Path

from pydantic import PostgresDsn, field_validator
from pydantic_core.core_schema import FieldValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    snapshot: Path  # Path to the openalex-snapshot root
    last_update_file: Path  # Path to a file that only contains the date of the last update (YYYY-MM-DD)
    last_update: str | None = None

    solr_host: str = 'localhost'  # solr host
    solr_port: int = 8983
    solr_collection: str = 'openalex'  # Solr collection
    solr_bin: Path  # Path to solr bin directory
    solr_url: str | None = None

    pg_scheme: str = 'postgresql'
    pg_host: str = 'localhost'  # host of the db server
    pg_port: int = 5432  # port of the db server
    pg_user: str = 'openalex'  # username for the database
    pg_pw: str  # password for the database user
    pg_db: str = 'openalex'  # name of the database
    pg_schema: str = 'openalex'  # name of database schema

    postgres: PostgresDsn | None = None

    @field_validator('postgres', mode='before')
    def build_connection_string(cls, v: str | None, info: FieldValidationInfo) -> str:
        assert info.config is not None

        if isinstance(v, str):
            return v

        return PostgresDsn.build(
            scheme=info.data.get('pg_scheme', 'postgresql'),
            username=info.data.get('pg_user'),
            password=info.data.get('pg_pw'),
            host=info.data.get('pg_host'),
            port=info.data.get('pg_port'),
            path=f'/{info.data.get("pg_db", "")}',
        )

    @field_validator('last_update', mode='before')
    def load_last_updated(cls, v: str | None, info: FieldValidationInfo) -> str:
        assert info.config is not None

        if isinstance(v, str):
            return v

        fname: Path = info.data.get('last_update_file')
        if fname is not None and fname.exists():
            with open(fname, 'r') as f:
                return f.read().strip()
        else:
            return '1970-01-01'

    @field_validator('solr_url', mode='before')
    def create_solr_url(cls, v: str | None, info: FieldValidationInfo) -> str:
        assert info.config is not None

        if isinstance(v, str):
            return v

        return f'http://{info.data.get("solr_host")}:{info.data.get("solr_port")}' \
               f'/solr/{info.data.get("solr_collection")}'

    model_config = SettingsConfigDict(env_prefix='oa_',
                                      env_file_encoding='utf-8')


conf_file = os.environ.get('OA_CONFIG', './default.env')
settings = Settings(_env_file=conf_file, _env_file_encoding='utf-8')
