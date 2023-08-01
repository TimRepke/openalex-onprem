from msgspec import Struct


class InvertedAbstract(Struct):
    IndexLength: int
    InvertedIndex: dict[str, list[int]]


class WorkIds(Struct, omit_defaults=True):
    # doi: str | None = None # redundant with Work.doi
    mag: int | None = None
    # openalex: str
    pmid: str | None = None
    pmcid: str | None = None


class Biblio(Struct, omit_defaults=True):
    volume: str | None = None
    issue: str | None = None
    first_page: str | None = None
    last_page: str | None = None


class DehydratedInstitution(Struct, kw_only=True, omit_defaults=True):
    country_code: str | None = None
    display_name: str | None = None
    id: str | None = None
    ror: str | None = None
    type: str | None = None


class DehydratedAuthor(Struct, omit_defaults=True):
    display_name: str | None = None
    id: str | None = None
    orcid: str | None = None


class Authorship(Struct):
    author: DehydratedAuthor | None = None
    author_position: str | None = None
    institutions: list[DehydratedInstitution] | None = None
    is_corresponding: bool | None = None
    raw_affiliation_string: str | None = None


class DehydratedSource(Struct, omit_defaults=True, kw_only=True):
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


class Location(Struct, omit_defaults=True, kw_only=True):
    is_oa: bool | None = None
    landing_page_url: str | None = None
    license: str | None = None
    source: DehydratedSource | None = None
    pdf_url: str | None = None
    version: str | None = None


class Work(Struct, kw_only=True, omit_defaults=True):
    abstract_inverted_index: str | None = None
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
    # counts_by_year
    created_date: str | None = None
    display_name: str | None = None
    doi: str | None = None

    # grants
    id: str | None = None
    ids: WorkIds | None = None
    is_oa: bool | None = None
    is_paratext: bool | None = None
    is_retracted: bool | None = None
    language: str | None = None
    # license:str
    locations: list[Location] | None = None
    # locations_count
    # mesh
    # ngrams_url
    # open_access
    # primary_location
    publication_date: str | None = None
    publication_year: int | None = None
    # referenced_works
    # related_works
    title: str | None = None
    type: str | None = None
    # type_crossref
    updated_date: str | None = None
    # ngram
    # ngram_count
    # ngram_tokens
    # term_frequency


class WorkOut(Struct, kw_only=True, omit_defaults=True):
    id: str
    display_name: str | None = None
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

    is_oa: bool | None = None
    is_paratext: bool | None = None
    is_retracted: bool | None = None
    language: str | None = None

    locations: str | None = None  # list[Location]

    publication_date: str | None = None
    publication_year: int | None = None
    type: str | None = None
    updated_date: str | None = None
