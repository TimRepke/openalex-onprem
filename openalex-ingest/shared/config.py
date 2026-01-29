import os
import json
from typing import Any
from pathlib import Path

from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from nacsos_data.util.conf import OpenAlexConfig, DatabaseConfig


class ServerSettings(BaseModel):
    HOST: str = 'localhost'  # host to run this server on
    PORT: int = 8080  # port for this serve to listen at
    DEBUG_MODE: bool = False  # set this to true in order to get more detailed logs
    WORKERS: int = 2  # number of worker processes
    WEB_URL: str = 'https://localhost'  # URL to the web frontend (without trailing /)
    OPENAPI_FILE: str = '/openapi.json'  # absolute URL path to openapi.json file
    OPENAPI_PREFIX: str = ''  # see https://fastapi.tiangolo.com/advanced/behind-a-proxy/
    ROOT_PATH: str = ''  # see https://fastapi.tiangolo.com/advanced/behind-a-proxy/

    HEADER_CORS: bool = False  # set to true to allow CORS
    HEADER_TRUSTED_HOST: bool = False  # set to true to allow hosts from any origin
    CORS_ORIGINS: list[str] = []  # list of trusted hosts

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


class Settings(BaseSettings):
    CACHE_API = ServerSettings  # fastapi server settings
    CACHE_DB = DatabaseConfig  # meta-cache database
    DB = DatabaseConfig  # NACSOS-core database
    OPENALEX = OpenAlexConfig  # OpenAlex (solr/api) config

    REDIS_URL: str = 'redis://localhost:6379'
    RESULT_LIMIT: int = 100

    QUEUE_RUNTIME_LIMIT: int = 4 * 60  # queue worker is called every 5 min, let it work for 4 minutes in between

    LOG_CONF_FILE: str = 'config/logging.toml'
    LOGGING_CONF: dict[str, Any] | None = None

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_prefix='NACSOS_',
        env_nested_delimiter='__',
        extra='allow',
    )


def load_settings(conf_file: str | None = None) -> Settings:
    if conf_file is None:
        conf_file = os.environ.get('OACACHE_CONFIG', 'config/default.env')
    if not Path(conf_file).is_file():
        raise FileNotFoundError(f'Configuration file not found: {conf_file}')
    return Settings(_env_file=conf_file, _env_file_encoding='utf-8')  # type: ignore[call-arg]
