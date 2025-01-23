from meta_cache.handlers.db import DatabaseEngine
from meta_cache.config import settings

db_engine = DatabaseEngine(host=settings.DB_HOST,
                           port=settings.DB_PORT,
                           user=settings.DB_USER,
                           password=settings.DB_PASSWORD,
                           database=settings.DB_DATABASE,
                           debug=settings.DEBUG_MODE)
