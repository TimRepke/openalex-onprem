import mimetypes
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from rq_dashboard_fast import RedisQueueDashboard

from meta_cache.config import settings

from .middleware import TimingMiddleware, ErrorHandlingMiddleware
from .api import router as api_router
from .logger import get_logger
from .db import db_engine
from .queue import queues

mimetypes.init()

logger = get_logger('meta-cache.server')


@asynccontextmanager
async def lifespan(api_app: FastAPI):
    # Following code executed on startup
    logger.info('Setting up DB engine')
    db_engine.startup()
    logger.info(f'Created queues: {queues.keys()}')

    yield  # running server

    # Following code executed after shutdown
    # [shutdown code]


app = FastAPI(
    openapi_url=settings.OPENAPI_FILE,
    openapi_prefix=settings.OPENAPI_PREFIX,
    root_path=settings.ROOT_PATH,
    separate_input_output_schemas=False,
    lifespan=lifespan
)

logger.debug('Setting up server and middlewares')
mimetypes.add_type('application/javascript', '.js')

app.add_middleware(ErrorHandlingMiddleware)
if settings.HEADER_TRUSTED_HOST:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.CORS_ORIGINS)
    logger.info(f'TrustedHostMiddleware allows the following hosts: {settings.CORS_ORIGINS}')
if settings.HEADER_CORS:
    app.add_middleware(CORSMiddleware,
                       allow_origins=settings.CORS_ORIGINS,
                       allow_methods=['GET', 'POST', 'DELETE', 'POST', 'PUT', 'OPTIONS'],
                       allow_headers=['*'],
                       allow_credentials=True)
    logger.info(f'CORSMiddleware will accept the following origins: {settings.CORS_ORIGINS}')
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(TimingMiddleware)

logger.debug('Setup routers')
app.include_router(api_router, prefix='/api')

app.mount('/rq', RedisQueueDashboard(settings.REDIS_URL, '/rq'))

# app.mount('/', StaticFiles(directory=settings.SERVER.STATIC_FILES, html=True), name='static')
