import re
import uuid
from typing import Any, Annotated
from datetime import datetime

from pydantic import BaseModel, AfterValidator
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import DateTime, func, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from nacsos_data.util.academic.apis import APIEnum

from .models import SourcePriority, OnConflict

NAMING_CONVENTION = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}

metadata = SQLModel.metadata
metadata.naming_convention = NAMING_CONVENTION

URLS = re.compile(
    r'(https://openalex.org/'
    r'|https://orcid.org/'
    r'|https://doi.org/'
    r'|https://www.wikidata.org/wiki/'
    r'|https://ror.org/)',
)


def strip_url(url: str | None) -> str | None:
    if url is None:
        return None
    return URLS.sub('', url)


class Request(SQLModel, table=True):
    __tablename__ = 'request'
    record_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True, unique=True, nullable=False)

    wrapper: str = Field(nullable=False, unique=False, index=True)
    api_key_id: uuid.UUID | None = Field(default=None, nullable=True, foreign_key='api_key.api_key_id')

    openalex_id: Annotated[str | None, AfterValidator(strip_url)] = Field(default=None, nullable=True, unique=False, index=True)
    doi: Annotated[str | None, AfterValidator(strip_url)] = Field(default=None, nullable=True, unique=False, index=True)

    pubmed_id: str | None = Field(default=None, nullable=True, unique=False, index=True)
    s2_id: str | None = Field(default=None, nullable=True, unique=False, index=True)
    scopus_id: str | None = Field(default=None, nullable=True, unique=False, index=True)
    wos_id: str | None = Field(default=None, nullable=True, unique=False, index=True)
    dimensions_id: str | None = Field(default=None, nullable=True, unique=False, index=True)
    nacsos_id: uuid.UUID | None = Field(default=None, nullable=True, unique=False, index=True)
    queue_id: int | None = Field(default=None, nullable=True, unique=False, index=False)  # Reference to Queue.queue_id

    title: str | None = None
    abstract: str | None = None

    solarized: bool | None = Field(default=None, nullable=True, unique=False, index=False)
    time_created: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), index=False),
        default_factory=datetime.now,
    )

    # found: bool = GENERATED ALWAYS AS (raw IS NOT NULL) STORED
    raw: dict[str, Any] | None = Field(sa_column=Column(MutableDict.as_mutable(JSONB(none_as_null=True))), default=None)


class Queue(SQLModel, table=True):
    __tablename__ = 'queue'
    queue_id: int | None = Field(default=None, primary_key=True)

    doi: Annotated[str | None, AfterValidator(strip_url)] = Field(default=None, nullable=True, unique=False, index=False)
    openalex_id: Annotated[str | None, AfterValidator(strip_url)] = Field(default=None, nullable=True, unique=False, index=False)
    pubmed_id: str | None = Field(default=None, nullable=True, unique=False, index=False)
    s2_id: str | None = Field(default=None, nullable=True, unique=False, index=False)
    scopus_id: str | None = Field(default=None, nullable=True, unique=False, index=False)
    wos_id: str | None = Field(default=None, nullable=True, unique=False, index=False)
    dimensions_id: str | None = Field(default=None, nullable=True, unique=False, index=False)
    nacsos_id: uuid.UUID | None = Field(default=None, nullable=True, unique=False, index=False)

    sources: list[tuple[APIEnum, SourcePriority]] | None = Field(sa_column=Column(MutableDict.as_mutable(JSONB(none_as_null=True))), default=None)
    on_conflict: OnConflict = Field(default=OnConflict.DO_NOTHING, nullable=False, unique=False, index=False)

    time_created: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), index=False),
        default_factory=datetime.now,
    )


class QueueRequests(BaseModel):  # FIXME: class QueueRequests(Queue, table=False) throws type error
    # begin inheritance hack
    queue_id: int | None = None

    doi: Annotated[str | None, AfterValidator(strip_url)] = None
    openalex_id: Annotated[str | None, AfterValidator(strip_url)] = None
    pubmed_id: str | None = None
    s2_id: str | None = None
    scopus_id: str | None = None
    wos_id: str | None = None
    dimensions_id: str | None = None
    nacsos_id: uuid.UUID | None = None

    sources: list[tuple[APIEnum, SourcePriority]] | None = None
    on_conflict: OnConflict = OnConflict.DO_NOTHING

    time_created: datetime
    source: APIEnum
    #  end hack

    priority: SourcePriority
    num_has_request: int
    num_has_abstract: int
    num_has_title: int
    num_has_raw: int
    num_has_source_request: int
    num_has_source_abstract: int
    num_has_source_title: int
    num_has_source_raw: int

    @property
    def info_str(self) -> str:
        return ', '.join(
            [f'on-conflict: {self.on_conflict}']
            + [f'{key}: {getattr(self, key)}' for key in sorted(set(QueueRequests.model_fields.keys()) - set(Queue.model_fields.keys()))],
        )


class AuthApiKeyLink(SQLModel, table=True):
    __tablename__ = 'm2m_auth_api_key'
    api_key_id: uuid.UUID | None = Field(default=None, foreign_key='api_key.api_key_id', primary_key=True)
    auth_key_id: uuid.UUID | None = Field(default=None, foreign_key='auth_key.auth_key_id', primary_key=True)


class ApiKey(SQLModel, table=True):
    __tablename__ = 'api_key'
    api_key_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True, unique=True, nullable=False)

    owner: str | None = None
    wrapper: str | None = None
    api_key: str | None = None
    proxy: str | None = None
    active: bool = True

    last_used: datetime | None = Field(sa_column=Column(DateTime(timezone=True), onupdate=func.now()), default=None)
    api_feedback: dict[str, Any] | None = Field(sa_column=Column(MutableDict.as_mutable(JSONB(none_as_null=True))), default=None)

    auth_keys: list['AuthKey'] = Relationship(back_populates='api_keys', link_model=AuthApiKeyLink)


class AuthKey(SQLModel, table=True):
    __tablename__ = 'auth_key'
    auth_key_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        unique=True,
        nullable=False,
    )

    note: str
    active: bool = True

    read: bool = False
    write: bool = False

    api_keys: list['ApiKey'] = Relationship(back_populates='auth_keys', link_model=AuthApiKeyLink)
