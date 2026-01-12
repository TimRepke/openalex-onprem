import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Generator

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlmodel import text, select, or_

from ..db import DatabaseEngine
from ..models import CacheResponse, Reference, ResponseRecord
from ..schema import Request, ApiKey
from ..util import get_reference_df, mark_status

logger = logging.getLogger('wrapper.base')


class classproperty(property):
    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


class AbstractWrapper(ABC):
    @classproperty
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def db_field_id(self) -> str:
        pass

    @classproperty
    def db_id_fields(cls) -> list[str]:
        return [cls.db_field_id, 'openalex_id', 'doi']

    @staticmethod
    @abstractmethod
    def get_title(obj: dict[str, Any]) -> str | None:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def get_abstract(obj: dict[str, Any]) -> str | None:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def get_doi(obj: dict[str, Any]) -> str | None:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def get_id(obj: dict[str, Any]) -> str | None:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def fetch(db_engine: DatabaseEngine, references: list[Reference], auth_key: str) -> Generator[Request, None, None]:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def _api_key_query_extra() -> str:
        raise NotImplementedError()

    @classmethod
    def get_api_keys(cls, db_engine: DatabaseEngine, auth_key: str) -> list[ApiKey]:
        with db_engine.session() as session:
            stmt = text(f'''
                SELECT api_key.*
                FROM api_key
                     JOIN m2m_auth_api_key ON api_key.api_key_id = m2m_auth_api_key.api_key_id
                     JOIN auth_key ON m2m_auth_api_key.auth_key_id = auth_key.auth_key_id
                WHERE auth_key.auth_key_id = :auth_key
                  AND auth_key.active IS TRUE
                  AND api_key.active IS TRUE
                  AND api_key.wrapper = :wrapper
                  {cls._api_key_query_extra()}
                ORDER BY last_used;''')
            keys = session.exec(stmt, params={
                'wrapper': cls.name,
                'auth_key': auth_key,
            }).all()
            if keys is None or len(keys) == 0:
                raise PermissionError(f'No valid {cls.name} API key available for this user!')
            return [ApiKey.model_validate(key) for key in keys]

    @staticmethod
    @abstractmethod
    def log_api_key_use(db_engine: DatabaseEngine, key: ApiKey) -> None:
        raise NotImplementedError()

    @classmethod
    def run(cls,
            db_engine: DatabaseEngine,
            references: list[Reference],
            auth_key: str,
            fail_on_error: bool = False,
            skip_existing: bool = True,
            ) -> CacheResponse:
        # Construct tracker for missed IDs
        df = get_reference_df(references)

        def complete_ids(rec: Request) -> Request:
            for fld, val in Reference.ids(rec):
                for _, ref in df[df[fld] == val].iterrows():
                    for ref_field in Reference.keys():
                        if ref[ref_field] is not None and getattr(rec, ref_field) is None:
                            setattr(rec, ref_field, ref[ref_field])
            return rec

        found = []
        with db_engine.session() as session:
            if skip_existing:
                stmt = (
                    select(*[getattr(Request, field) for field in cls.db_id_fields])
                    .where(and_(
                        Request.wrapper == cls.name,
                        or_(*[getattr(Request, field) == value
                              for reference in references
                              for field, value in Reference.ids(reference)])))
                    .limit(df[Reference.keys()].notna().to_numpy().sum() * 2)
                )
                existing = session.exec(stmt).all()
                references = [
                    reference
                    for reference in references
                    if all([
                        getattr(record, field) != getattr(reference, field)
                        for record in existing
                        for field in cls.db_id_fields
                    ])
                ]

            # Contact API and start fetching data
            results = cls.fetch(db_engine=db_engine, references=references, auth_key=auth_key)

            for record in results:
                # Add missing IDs from the requested references to record
                record = complete_ids(record)

                mark_status(df, record, status='added')
                found.append(record)
                session.add(record)

                try:
                    session.commit()
                except IntegrityError as e:
                    if fail_on_error:
                        raise e
                    logger.exception(e)
                    logger.warning('Ignoring errors!')
                    session.rollback()

            logger.debug(f'Missed {(df['missed'] == True).sum():,} references, going to record this in DB')
            # Persist that we requested this (missing)
            for _, missed in df[df['missed'] == True].iterrows():
                missed_record = Request(**dict(Reference.ids(missed)))
                missed_record.wrapper = cls.name
                # missed_record.wrapper = auth_key
                session.add(missed_record)
            session.commit()

        return CacheResponse(
            references=[ResponseRecord(**rec) for rec in df.to_dict(orient='records')],
            records=found,
            n_added=df['added'].sum(),
            n_missed=df['missed'].sum(),
            n_queued=0,
            n_hits=0,
        )
