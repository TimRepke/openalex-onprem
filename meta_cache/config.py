import os

from .setup import Settings


conf_file = os.environ.get('OACACHE_CONFIG', 'config/default.env')
settings = Settings(_env_file=conf_file, _env_file_encoding='utf-8')  # type: ignore[call-arg]

__all__ = ['settings', 'conf_file']
