import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_json import mutable_json_type
from sqlmodel import Field, SQLModel


class Record(SQLModel, table=True):
    __tablename__ = 'record'
    record_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True, unique=True, nullable=False)

    wos_id: str | None = Field(default=None, nullable=True, unique=True, index=True)
    scopus_id: str | None = Field(default=None, nullable=True, unique=True, index=True)
    openalex_id: str | None = Field(default=None, nullable=True, unique=True, index=True)
    s2_id: str | None = Field(default=None, nullable=True, unique=True, index=True)
    pubmed_id: str | None = Field(default=None, nullable=True, unique=True, index=True)
    dimensions_id: str | None = Field(default=None, nullable=True, unique=True, index=True)
    doi: str | None = Field(default=None, nullable=True, unique=False, index=True)

    title: str | None = None
    abstract: str | None = None

    requested_s2: bool | None = Field(default=None, nullable=True, unique=False, index=True)
    requested_openalex: bool | None = Field(default=None, nullable=True, unique=False, index=True)
    requested_dimensions: bool | None = Field(default=None, nullable=True, unique=False, index=True)
    requested_scopus: bool | None = Field(default=None, nullable=True, unique=False, index=True)
    requested_wos: bool | None = Field(default=None, nullable=True, unique=False, index=True)
    requested_other: bool | None = Field(default=None, nullable=True, unique=False, index=True)

    time_created: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=func.now(), index=True),
                                   default_factory=datetime.now)
    time_updated: datetime | None = Field(sa_column=Column(DateTime(timezone=True), onupdate=func.now()), default=None)
    time_s2: datetime | None = Field(sa_column=Column(DateTime(timezone=True)), default=None)
    time_openalex: datetime | None = Field(sa_column=Column(DateTime(timezone=True)), default=None)
    time_dimensions: datetime | None = Field(sa_column=Column(DateTime(timezone=True)), default=None)
    time_scopus: datetime | None = Field(sa_column=Column(DateTime(timezone=True)), default=None)
    time_wos: datetime | None = Field(sa_column=Column(DateTime(timezone=True)), default=None)
    time_other: datetime | None = Field(sa_column=Column(DateTime(timezone=True)), default=None)

    raw_s2: dict[str, Any] | None = Field(sa_column=Column(mutable_json_type(dbtype=JSONB(none_as_null=True),
                                                                             nested=True)), default=None)
    raw_openalex: dict[str, Any] | None = Field(sa_column=Column(mutable_json_type(dbtype=JSONB(none_as_null=True),
                                                                                   nested=True)), default=None)
    raw_dimensions: dict[str, Any] | None = Field(sa_column=Column(mutable_json_type(dbtype=JSONB(none_as_null=True),
                                                                                     nested=True)), default=None)
    raw_scopus: dict[str, Any] | None = Field(sa_column=Column(mutable_json_type(dbtype=JSONB(none_as_null=True),
                                                                                 nested=True)), default=None)
    raw_wos: dict[str, Any] | None = Field(sa_column=Column(mutable_json_type(dbtype=JSONB(none_as_null=True),
                                                                              nested=True)), default=None)
    raw_other: dict[str, Any] | None = Field(sa_column=Column(mutable_json_type(dbtype=JSONB(none_as_null=True),
                                                                                nested=True)), default=None)


class ApiKey(SQLModel, table=True):
    __tablename__ = 'api_key'
    api_key_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True, unique=True, nullable=False)

    owner: str | None = None
    wrapper: str | None = None
    api_key: str | None = None

    last_used: datetime | None = Field(sa_column=Column(DateTime(timezone=True), onupdate=func.now()), default=None)
    requests_limit: int | None = None
    requests_remaining: int | None = None
    requests_reset: str | None = None

    active: bool = True
