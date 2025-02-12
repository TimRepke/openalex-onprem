import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Generator

from sqlalchemy.exc import IntegrityError
from sqlmodel import text, select, or_

from ..db import DatabaseEngine
from ..models import CacheResponse, Reference, ResponseRecord
from ..schema import Record, ApiKey
from ..util import get_reference_df, mark_status

logger = logging.getLogger('wrapper.base')


class AbstractWrapper(ABC):
    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def db_field_requested(self):
        pass

    @property
    @abstractmethod
    def db_field_time(self):
        pass

    @property
    @abstractmethod
    def db_field_raw(self):
        pass

    @property
    @abstractmethod
    def db_field_id(self):
        pass

    @property
    def db_id_fields(self):
        return [self.db_field_id, 'openalex_id', 'doi']

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
    def fetch(db_engine: DatabaseEngine, references: list[Reference], auth_key: str) -> Generator[Record, None, None]:
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
            override_fields: bool = False,
            ) -> CacheResponse:
        # Construct tracker for missed IDs
        df = get_reference_df(references)

        def complete_ids(rec: Record) -> Record:
            for fld, val in Reference.ids(rec):
                for _, ref in df[df[fld] == val].iterrows():
                    for ref_field in Reference.keys():
                        if ref[ref_field] is not None and getattr(rec, ref_field) is None:
                            setattr(rec, ref_field, ref[ref_field])
            return rec

        found = []
        with db_engine.session() as session:
            # Contact API and start fetching data
            results = cls.fetch(db_engine=db_engine, references=references, auth_key=auth_key)

            for record in results:
                # Add missing IDs from the requested references to record
                record = complete_ids(record)

                # Record that we found something and construct SQL query
                ors = []
                for field, value in Reference.ids(record):
                    df.loc[df[field] == value, 'missed'] = False
                    ors.append(getattr(Record, field) == value)

                # Query database to fetch existing record
                if len(ors) > 0:
                    existing = session.exec(select(Record).where(or_(*ors))).all()
                else:
                    existing = []

                # Record did not exist yet in the database
                if len(existing) == 0:
                    mark_status(df, record, status='added')
                    found.append(record)
                    session.add(record)
                else:
                    # fill all empty fields in existing records that we now have data for
                    for ex_record in existing:
                        for field in Record.model_fields.keys():
                            if field == 'record_id':  # ignore primary key
                                continue
                            if getattr(record, field) is not None and (override_fields or
                                                                       getattr(ex_record, field) is None):
                                setattr(ex_record, field, getattr(record, field))
                        ex_record.time_updated = datetime.now()
                        found.append(ex_record)
                        session.add(ex_record)
                    mark_status(df, record, status='updated')
                try:
                    session.commit()
                except IntegrityError as e:
                    if fail_on_error:
                        raise e
                    logger.exception(e)
                    logger.warning('Ignoring errors!')
                    session.rollback()

            # Persist that we requested this (missing)
            for _, missed in df[df['missed'] == True].iterrows():
                missed_record = Record(**dict(Reference.ids(missed)))
                setattr(missed_record, cls.db_field_requested, True)
                setattr(missed_record, cls.db_field_time, datetime.now())
                session.add(missed_record)
            session.commit()

        return CacheResponse(
            references=[ResponseRecord(**rec) for rec in df.to_dict(orient='records')],
            records=found,
            n_added=df['added'].sum(),
            n_updated=df['hit'].sum(),
            n_missed=df['missed'].sum(),
            n_queued=0,
            n_hits=0,
        )
