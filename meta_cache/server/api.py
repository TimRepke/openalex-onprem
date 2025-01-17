from fastapi import APIRouter
from sqlalchemy import select

from meta_cache.data.schema import Record
from meta_cache.server.db import db_engine
from meta_cache.wrappers import Request

router = APIRouter()


@router.post('/lookup', response_model=list[Record])
async def lookup(req: Request) -> list[Record]:
    pass
