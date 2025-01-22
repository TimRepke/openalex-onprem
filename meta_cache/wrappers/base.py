from abc import ABC, abstractmethod

from typing import Any, Generator

from sqlalchemy import text, select, or_

from meta_cache.data import DatabaseEngine, Query, Record, ApiKey, Response


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
    def _api_key_query_extra() -> str:
        raise NotImplementedError()

    @classmethod
    def get_api_keys(cls, db_engine: DatabaseEngine, auth_key: str) -> list[ApiKey]:
        with db_engine.session() as session:
            stmt = text(f'''
                SELECT *
                FROM api_key
                     JOIN m2m_auth_api_key ON api_key.api_key_id = m2m_auth_api_key.api_key_id
                     JOIN auth_key ON m2m_auth_api_key.auth_key_id = auth_key.auth_key_id
                WHERE auth_key.auth_key_id = :auth_key
                  AND auth_key.active IS TRUE
                  AND api_key.active IS TRUE
                  AND api_key.wrapper = :wrapper
                  {cls._api_key_query_extra()}
                ORDER BY last_used;''')
            key = session.exec(stmt, params={
                'wrapper': cls.name,
                'auth_key': auth_key,
            })
            if key is None or len(key) == 0:
                raise PermissionError(f'No valid {cls.name} API key available for this user!')
            return key

    @staticmethod
    def log_api_key_use(db_engine: DatabaseEngine, key: ApiKey) -> None:
        with db_engine.session() as session:
            session.add(key)
            session.commit()

    @staticmethod
    @abstractmethod
    def fetch(db_engine: DatabaseEngine, query: Query, auth_key: str) -> Generator[Record, None, None]:
        raise NotImplementedError()

    @classmethod
    def ensure_cached(cls, db_engine: DatabaseEngine, query: Query, auth_key: str) -> Response:
        # Construct tracker for missed IDs
        missed: dict[str, set[str]] = {}
        for field in Query.model_fields.keys():
            ids = getattr(query, field)
            if ids is not None and len(ids) > 0:
                missed[field] = set(ids)

        # Contact API and fetch data
        results = list(cls.fetch(db_engine=db_engine, query=query, auth_key=auth_key))
        found = []
        with db_engine.session() as session:
            for record in results:
                record_ids = {
                    field: getattr(record, field)
                    for field in Query.model_fields.keys()
                    if getattr(record, field) is not None
                }

                existing = session.exec(
                    select(Record)
                    .where(or_([
                        getattr(Record, field) == value
                        for field, value in record_ids.items()
                    ]))
                )

                if len(existing) == 0:
                    found.append(record)
                    session.add(record)

                for ex_record in existing:
                    for field in Record.model_fields.keys():
                        if getattr(record, field) is not None and getattr(ex_record, field) is None:
                            setattr(ex_record, field, getattr(record, field))
                    found.append(ex_record)
                    session.add(ex_record)
                session.commit()

                # Strike off our missing tracker
                for field, value in record_ids.items():
                    missed[field].discard(value)

            # Persist that we requested this (missing)
            for

        return Response(
            found=results,
            missed=Query(**missed),
        )
