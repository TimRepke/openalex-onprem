from pydantic import BaseModel, ConfigDict

FIELDS_TO_FETCH = [
    'id',
    'doi',
    'title',
    'display_name',
    'publication_year',
    'publication_date',
    'ids',
    'language',
    'primary_location',
    'type',
    'type_crossref',
    'indexed_in',
    'open_access',
    'authorships',
    # 'institution_assertions',
    # 'countries_distinct_count',
    # 'institutions_distinct_count',
    # 'corresponding_author_ids',
    # 'corresponding_institution_ids',
    'apc_list',
    'apc_paid',
    'fwci',
    'has_fulltext',
    'fulltext_origin',
    # 'cited_by_count',
    # 'citation_normalized_percentile',
    # 'cited_by_percentile_year',
    # 'biblio',
    'is_retracted',
    'is_paratext',
    # 'primary_topic',
    'topics',
    'keywords',
    # 'concepts',
    # 'mesh',
    # 'locations_count',
    'locations',
    'best_oa_location',
    # 'sustainable_development_goals',
    'grants',
    'datasets',
    # 'versions',
    # 'referenced_works_count',
    'referenced_works',
    # 'related_works',
    'abstract_inverted_index',
    # 'cited_by_api_url',
    # 'counts_by_year',
    'updated_date',
    'created_date'
]

from typing import Literal


class WorkIds(BaseModel):
    model_config = ConfigDict(extra='ignore')
    # doi: str | None = None # redundant with Work.doi
    mag: int | None = None
    # openalex: str
    pmid: str | None = None
    pmcid: str | None = None


class Biblio(BaseModel):
    model_config = ConfigDict(extra='ignore')
    volume: str | None = None
    issue: str | None = None
    first_page: str | None = None
    last_page: str | None = None


class DehydratedInstitution(BaseModel):
    model_config = ConfigDict(extra='ignore')
    country_code: str | None = None
    display_name: str | None = None
    id: str | None = None
    ror: str | None = None
    type: str | None = None
    lineage: list[str] | None = None


class DehydratedAuthor(BaseModel):
    model_config = ConfigDict(extra='ignore')
    display_name: str | None = None
    id: str | None = None
    orcid: str | None = None


class Authorship(BaseModel):
    model_config = ConfigDict(extra='ignore')
    author: DehydratedAuthor | None = None
    author_position: str | None = None
    countries: list[str] | None = None
    institutions: list[DehydratedInstitution] | None = None
    is_corresponding: bool | None = None
    raw_affiliation_string: str | None = None
    raw_affiliation_strings: list[str] | None = None
    raw_author_name: str | None = None


class DehydratedSource(BaseModel):
    model_config = ConfigDict(extra='ignore')
    display_name: str | None = None
    host_organization: str | None = None
    # host_organization_lineage
    host_organization_name: str | None = None
    id: str | None = None
    # is_in_doaj
    # is_oa
    issn: list[str] | None = None
    issn_l: str | None = None
    type: str | None = None


class Location(BaseModel):
    model_config = ConfigDict(extra='ignore')
    is_accepted: bool | None = None
    is_oa: bool | None = None
    is_published: bool | None = None
    landing_page_url: str | None = None
    license: str | None = None
    source: DehydratedSource | None = None
    pdf_url: str | None = None
    version: str | None = None


class LocationOut(BaseModel):
    model_config = ConfigDict(extra='ignore')
    is_accepted: bool | None = None
    is_oa: bool | None = None
    is_primary: bool | None = None
    is_published: bool | None = None
    landing_page_url: str | None = None
    license: str | None = None
    source: DehydratedSource | None = None
    pdf_url: str | None = None
    version: str | None = None


class TopicHierarchy(BaseModel):
    model_config = ConfigDict(extra='ignore')
    id: int | str | None = None
    display_name: str | None = None


class Topic(BaseModel):
    model_config = ConfigDict(extra='ignore')
    id: str | None = None
    display_name: str | None = None
    score: float | None = None
    subfield: TopicHierarchy | None = None
    field: TopicHierarchy | None = None
    domain: TopicHierarchy | None = None


OAStatus = Literal['diamond', 'gold', 'green', 'hybrid', 'bronze', 'closed']


class OpenAccess(BaseModel):
    model_config = ConfigDict(extra='ignore')
    any_repository_has_fulltext: bool | None = None
    is_oa: bool | None = None
    oa_status: str | None = None  # OAStatus
    oa_url: str | None = None


class Work(BaseModel):
    model_config = ConfigDict(extra='ignore')

    abstract_inverted_index: dict[str, list[int]] | None = None
    authorships: list[Authorship] | None = None
    # apc_list
    # apc_paid
    # best_oa_location
    biblio: Biblio | None = None
    # cited_by_api_url
    cited_by_count: int | None = None
    # concepts
    # corresponding_author_ids
    # corresponding_institution_ids
    countries_distinct_count: int | None = None
    # counts_by_year
    created_date: str | None = None
    display_name: str | None = None
    doi: str | None = None
    fulltext_origin: str | None = None
    # grants
    has_fulltext: bool | None = None
    # indexed_in
    id: str | None = None
    ids: WorkIds | None = None
    indexed_in: list[str] | None = None
    institutions_distinct_count: int | None = None
    is_authors_truncated: bool | None = None
    # is_oa: bool | None = None
    is_paratext: bool | None = None
    is_retracted: bool | None = None
    language: str | None = None
    # license
    locations: list[Location] | None = None
    # locations_count
    # mesh
    # ngrams_url
    open_access: OpenAccess | None = None
    primary_location: Location | None = None
    # primary_topic
    publication_date: str | None = None
    publication_year: int | None = None
    referenced_works: list[str] | None = None
    # related_works
    # sustainable_development_goals
    title: str | None = None
    topics: list[Topic] | None = None
    type: str | None = None
    # type_crossref
    updated_date: str | None = None


class WorkOut(BaseModel):
    model_config = ConfigDict(extra='ignore')

    id: str
    # display_name: str | None = None
    title: str | None = None
    abstract: str | None = None
    title_abstract: str | None = None

    authorships: str | None = None  # list[Authorship]
    biblio: str | None = None  # Biblio
    cited_by_count: int | None = None
    created_date: str | None = None
    doi: str | None = None
    mag: str | None = None
    pmid: str | None = None
    pmcid: str | None = None

    indexed_in: str | None = None
    external_abstract: bool | None = None
    is_oa: bool | None = None
    is_paratext: bool | None = None
    is_retracted: bool | None = None
    is_published: bool | None = None
    is_accepted: bool | None = None
    language: str | None = None

    publisher: str | None = None
    publisher_id: str | None = None
    source: str | None = None
    source_id: str | None = None

    locations: str | None = None  # list[Location]
    topics: str | None = None  # list[Topic]
    references: str | None = None  # list[str]

    publication_date: str | None = None
    publication_year: int | None = None
    type: str | None = None
    updated_date: str | None = None
