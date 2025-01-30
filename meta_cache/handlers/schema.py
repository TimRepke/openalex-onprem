import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_json import mutable_json_type
from sqlmodel import Field, SQLModel, Relationship


class Record(SQLModel, table=True):
    __tablename__ = 'record'
    record_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True, unique=True, nullable=False)

    dimensions_id: str | None = Field(default=None, nullable=True, unique=False, index=True)
    doi: str | None = Field(default=None, nullable=True, unique=False, index=True)
    openalex_id: str | None = Field(default=None, nullable=True, unique=False, index=True)
    pubmed_id: str | None = Field(default=None, nullable=True, unique=False, index=True)
    s2_id: str | None = Field(default=None, nullable=True, unique=False, index=True)
    scopus_id: str | None = Field(default=None, nullable=True, unique=False, index=True)
    wos_id: str | None = Field(default=None, nullable=True, unique=False, index=True)

    title: str | None = None
    abstract: str | None = None

    # NULL if never requested from API, True if requested and found record, False if requested and not found
    requested_dimensions: bool | None = Field(default=None, nullable=True, unique=False, index=True)
    requested_openalex: bool | None = Field(default=None, nullable=True, unique=False, index=True)
    requested_pubmed: bool | None = Field(default=None, nullable=True, unique=False, index=True)
    requested_s2: bool | None = Field(default=None, nullable=True, unique=False, index=True)
    requested_scopus: bool | None = Field(default=None, nullable=True, unique=False, index=True)
    requested_wos: bool | None = Field(default=None, nullable=True, unique=False, index=True)
    requested_other: bool | None = Field(default=None, nullable=True, unique=False, index=True)

    time_created: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=func.now(), index=True),
                                   default_factory=datetime.now)
    time_updated: datetime | None = Field(sa_column=Column(DateTime(timezone=True), onupdate=func.now()), default=None)
    time_dimensions: datetime | None = Field(sa_column=Column(DateTime(timezone=True)), default=None)
    time_pubmed: datetime | None = Field(sa_column=Column(DateTime(timezone=True)), default=None)
    time_openalex: datetime | None = Field(sa_column=Column(DateTime(timezone=True)), default=None)
    time_s2: datetime | None = Field(sa_column=Column(DateTime(timezone=True)), default=None)
    time_scopus: datetime | None = Field(sa_column=Column(DateTime(timezone=True)), default=None)
    time_wos: datetime | None = Field(sa_column=Column(DateTime(timezone=True)), default=None)
    time_other: datetime | None = Field(sa_column=Column(DateTime(timezone=True)), default=None)

    raw_dimensions: dict[str, Any] | None = Field(sa_column=Column(mutable_json_type(dbtype=JSONB(none_as_null=True),
                                                                                     nested=True)), default=None)
    raw_openalex: dict[str, Any] | None = Field(sa_column=Column(mutable_json_type(dbtype=JSONB(none_as_null=True),
                                                                                   nested=True)), default=None)
    raw_pubmed: dict[str, Any] | None = Field(sa_column=Column(mutable_json_type(dbtype=JSONB(none_as_null=True),
                                                                                 nested=True)), default=None)
    raw_s2: dict[str, Any] | None = Field(sa_column=Column(mutable_json_type(dbtype=JSONB(none_as_null=True),
                                                                             nested=True)), default=None)
    raw_scopus: dict[str, Any] | None = Field(sa_column=Column(mutable_json_type(dbtype=JSONB(none_as_null=True),
                                                                                 nested=True)), default=None)
    raw_wos: dict[str, Any] | None = Field(sa_column=Column(mutable_json_type(dbtype=JSONB(none_as_null=True),
                                                                              nested=True)), default=None)
    raw_other: dict[str, Any] | None = Field(sa_column=Column(mutable_json_type(dbtype=JSONB(none_as_null=True),
                                                                                nested=True)), default=None)


class AuthApiKeyLink(SQLModel, table=True):
    __tablename__ = 'm2m_auth_api_key'
    api_key_id: uuid.UUID | None = Field(default=None, foreign_key="api_key.api_key_id", primary_key=True)
    auth_key_id: uuid.UUID | None = Field(default=None, foreign_key="auth_key.auth_key_id", primary_key=True)


class ApiKey(SQLModel, table=True):
    __tablename__ = 'api_key'
    api_key_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True, unique=True, nullable=False)

    owner: str | None = None
    wrapper: str | None = None
    api_key: str | None = None
    proxy: str | None = None

    last_used: datetime | None = Field(sa_column=Column(DateTime(timezone=True), onupdate=func.now()), default=None)

    scopus_requests_limit: int | None = None
    scopus_requests_remaining: int | None = None
    scopus_requests_reset: str | None = None

    active: bool = True

    auth_keys: list['AuthKey'] = Relationship(back_populates='api_keys', link_model=AuthApiKeyLink)


class AuthKey(SQLModel, table=True):
    __tablename__ = 'auth_key'
    auth_key_id: uuid.UUID = Field(default_factory=uuid.uuid4,
                                   primary_key=True, index=True, unique=True, nullable=False)

    note: str
    active: bool = True

    read: bool = False
    write: bool = False

    api_keys: list['ApiKey'] = Relationship(back_populates='auth_keys', link_model=AuthApiKeyLink)
