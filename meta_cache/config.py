from typing import Any
import json
import toml
import os

from pydantic_settings import SettingsConfigDict, BaseSettings
from pydantic.networks import PostgresDsn
from pydantic import field_validator, ValidationInfo, AnyHttpUrl


class Settings(BaseSettings):
    HOST: str = 'localhost'  # host to run this server on
    PORT: int = 8080  # port for this serve to listen at
    DEBUG_MODE: bool = False  # set this to true in order to get more detailed logs
    WORKERS: int = 2  # number of worker processes
    WEB_URL: str = 'https://localhost'  # URL to the web frontend (without trailing /)
    OPENAPI_FILE: str = '/openapi.json'  # absolute URL path to openapi.json file
    OPENAPI_PREFIX: str = ''  # see https://fastapi.tiangolo.com/advanced/behind-a-proxy/
    ROOT_PATH: str = ''  # see https://fastapi.tiangolo.com/advanced/behind-a-proxy/

    RESULT_LIMIT: int = 100

    HEADER_CORS: bool = False  # set to true to allow CORS
    HEADER_TRUSTED_HOST: bool = False  # set to true to allow hosts from any origin
    CORS_ORIGINS: list[str] = []  # list of trusted hosts

    REDIS_URL: str = 'redis://localhost:6379'

    DB_SCHEME: str = 'postgresql'
    DB_SCHEMA: str = 'public'
    DB_HOST: str = 'localhost'  # host of the db server
    DB_PORT: int = 5432  # port of the db server
    DB_USER: str = 'meta_cache'  # username for the database
    DB_PASSWORD: str = 'secr€t_passvvord'  # password for the database user
    DB_DATABASE: str = 'meta_cache'  # name of the database

    DB_CONNECTION_STR: PostgresDsn | None = None

    @field_validator('DB_CONNECTION_STR', mode='before')
    def build_connection_string(cls, v: str | None, info: ValidationInfo) -> PostgresDsn:
        assert info.config is not None

        if isinstance(v, str):
            raise ValueError('This field will be generated automatically, please do not use it.')

        return PostgresDsn.build(
            scheme=info.data.get('DB_SCHEME', 'postgresql'),
            username=info.data.get('DB_USER'),
            password=info.data.get('DB_PASSWORD'),
            host=info.data.get('DB_HOST'),
            port=info.data.get('DB_PORT'),
            path=f'/{info.data.get("DB_DATABASE", "")}',
        )

    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> str | list[str]:
        if isinstance(v, str) and not v.startswith('['):
            return [i.strip() for i in v.split(',')]
        if isinstance(v, str) and v.startswith('['):
            ret = json.loads(v)
            if type(ret) is list:
                return ret
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # URL including path to OpenAlex collection
    OA_SOLR: AnyHttpUrl = 'http://localhost:8983/solr/openalex'  # type: ignore[assignment]

    LOG_CONF_FILE: str = 'config/logging.toml'
    LOGGING_CONF: dict[str, Any] | None = None

    @field_validator('LOGGING_CONF', mode='before')
    @classmethod
    def get_emails_enabled(cls, v: dict[str, Any] | None, info: ValidationInfo) -> dict[str, Any]:
        assert info.config is not None

        if isinstance(v, dict):
            return v
        filename: str = info.data.get('LOG_CONF_FILE', None)

        if filename is not None:
            with open(filename, 'r') as f:
                ret = toml.loads(f.read())
                if type(ret) is dict:
                    return ret
        raise ValueError('Logging config invalid!')

    model_config = SettingsConfigDict(case_sensitive=True, env_prefix='OACACHE_')


conf_file = os.environ.get('OACACHE_CONFIG', 'config/default.env')
settings = Settings(_env_file=conf_file, _env_file_encoding='utf-8')  # type: ignore[call-arg]

__all__ = ['settings', 'conf_file']
