from typing import Any
import pandas as pd

from .models import Reference
from .schema import Record


def get(obj: dict[str, Any], *keys, default: Any = None) -> Any | None:
    for key in keys:
        obj = obj.get(key)
        if obj is None:
            return default
    return obj


def get_reference_df(references: list[Reference]) -> pd.DataFrame:
    df = pd.DataFrame([ref.model_dump() for ref in references])

    # Extra fields for status tracking
    df['hit'] = None
    df['queued'] = None
    df['updated'] = None
    df['added'] = None
    # Set all as missed by default
    df['missed'] = True

    # Extra fields for cache hits
    df['record_id'] = None
    df['title'] = None
    df['abstract'] = None

    # Ensure all reference fields are there
    for field in (set(Reference.keys()) - set(df.columns)):
        df[field] = None

    return df


def mark_status(df: pd.DataFrame, record: Record, status: str = 'hit'):
    for field, value in Reference.ids(record):
        mask = df[field] == value
        df.loc[mask, 'missed'] = False
        df.loc[mask, status] = True
        if record.record_id:
            df.loc[mask, 'record_id'] = record.record_id
        if record.title:
            df.loc[mask, 'title'] = record.title
        if record.abstract:
            df.loc[mask, 'abstract'] = record.abstract
