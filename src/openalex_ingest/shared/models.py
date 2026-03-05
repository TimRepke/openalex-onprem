from enum import Enum
from typing import Any, Type, TypeVar

from pydantic import BeforeValidator


class SourcePriority(Enum):
    FORCE = 1  # definitely request with this source
    TRY = 2  # try request with this wrapper if a previous source hasn't found an abstract yet


class OnConflict(Enum):
    """
    Strategies to deal with the case, that the queue entry (based on DOI) already has an entry in the requests table
    """

    FORCE = 1  # don't check existing results, just work the queue entry (again) and add another request row
    DO_NOTHING = 2  # when we already asked for this DOI anywhere, don't try again
    RETRY_ABSTRACT = 3  # when we already asked for this DOI but have no abstract -> retry
    RETRY_RAW = 4  # when we already asked for this DOI but have no raw payload -> retry


T = TypeVar('T', bound=Enum)


def enum_validator(enum_type: Type[T]):
    def validator(v: Any) -> Any:
        # If it's already the right Enum type, leave it alone
        if isinstance(v, enum_type):
            return v

        # If it's a string, try to match by name or by its integer value
        if isinstance(v, str):
            # Try to match by name (e.g., "DO_NOTHING")
            if v in enum_type.__members__:
                return enum_type[v]
            # Try to see if it's a digit string (e.g., "1")
            if v.isdigit():
                return enum_type(int(v))

        # If it's an int, try to instantiate the Enum
        if isinstance(v, int):
            return enum_type(v)

        return v

    return BeforeValidator(validator)
