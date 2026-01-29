from enum import Enum


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
