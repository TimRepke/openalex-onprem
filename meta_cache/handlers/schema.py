import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_json import mutable_json_type
from sqlmodel import Field, SQLModel, Relationship


class Request(SQLModel, table=True):
    __tablename__ = 'request'
    record_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True, unique=True, nullable=False)

    wrapper: str = Field(nullable=False, unique=False, index=True)
    api_key_id: uuid.UUID | None = Field(default=None, nullable=True, foreign_key="api_key.api_key_id")

    openalex_id: str | None = Field(default=None, nullable=True, unique=False, index=True)
    doi: str | None = Field(default=None, nullable=True, unique=False, index=True)

    pubmed_id: str | None = Field(default=None, nullable=True, unique=False, index=True)
    s2_id: str | None = Field(default=None, nullable=True, unique=False, index=True)
    scopus_id: str | None = Field(default=None, nullable=True, unique=False, index=True)
    wos_id: str | None = Field(default=None, nullable=True, unique=False, index=True)
    dimensions_id: str | None = Field(default=None, nullable=True, unique=False, index=True)

    title: str | None = None
    abstract: str | None = None

    time_created: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=func.now(), index=True),
                                   default_factory=datetime.now)

    # found: bool = GENERATED ALWAYS AS (raw IS NOT NULL) STORED
    raw: dict[str, Any] | None = Field(sa_column=Column(mutable_json_type(dbtype=JSONB(none_as_null=True),
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

    dimensions_jwt: str | None = None

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
