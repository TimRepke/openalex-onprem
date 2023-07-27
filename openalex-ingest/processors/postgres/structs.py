from typing import Literal
from msgspec import Struct


class CountsByYear(Struct):
    year: int
    works_count: int
    cited_by_count: int


class FunderIds(Struct):
    openalex: str
    ror: str
    wikidata: str
    crossref: str
    doi: str


class Role(Struct):
    role: Literal['publisher', 'institution', 'funder']
    id: str
    works_count: int


class SummaryStats(Struct):
    yr_mean_citedness: float
    h_index: int
    i10_index: int


class Funder(Struct):
    alternate_titles: list[str]
    cited_by_count: int
    country_code: str
    counts_by_year: list[CountsByYear]
    created_date: str
    description: str
    display_name: str
    grants_count: int
    homepage_url: str
    id: str
    ids: FunderIds
    image_thumbnail_url: str
    image_url: str
    roles: list[Role]
    summary_stats: SummaryStats
    updated_date: str
    works_count: int


class PublisherIds(Struct):
    openalex: str
    ror: str
    wikidata: str


class Publisher(Struct):
    alternate_titles: list[str]
    cited_by_count: int
    country_codes: list[str]
    counts_by_year: CountsByYear
    created_date: str
    display_name: str
    hierarchy_level: int
    id: str
    ids: PublisherIds
    image_thumbnail_url: str
    image_url: str
    lineage: list[str]
    parent_publisher: str
    roles: list[Role]
    sources_api_url: str
    summary_stats: SummaryStats
    updated_date: str
    works_count: int


class DehydratedConcept(Struct):
    display_name: str
    id: str
    level: int
    wikidata: str


class RatedDehydratedConcept(Struct):
    display_name: str
    id: str
    level: int
    wikidata: str
    score: float


class ConceptIds(Struct):
    mag: int
    openalex: str
    umls_cui: list[str]
    umls_aui: list[str]
    wikidata: str
    wikipedia: str


class Concept(Struct):
    ancestors: list[DehydratedConcept]
    cited_by_count: int
    counts_by_year: CountsByYear
    created_date: str
    description: str
    display_name: str
    id: str
    ids: ConceptIds
    image_thumbnail_url: str
    image_url: str
    # international
    level: int
    related_concepts: list[RatedDehydratedConcept]
    summary_stats: SummaryStats
    updated_date: str
    wikidata: str
    works_api_url: str
    works_count: int


class DehydratedInstitution(Struct):
    country_code: str | None = None
    display_name: str | None = None
    id: str | None = None
    ror: str | None = None
    type: str | None = None


class RelatedDehydratedInstitution(Struct):
    country_code: str | None = None
    display_name: str | None = None
    id: str | None = None
    ror: str | None = None
    type: str | None = None
    relationship: Literal['parent', 'child', 'related']


class Geo(Struct):
    city: str
    geonames_city_id: str
    region: str
    country_code: str
    country: str
    latitude: float
    longitude: float


class InstitutionIds(Struct):
    openalex: str
    ror: str
    grid: str
    wikipedia: str
    wikidata: str
    mag: int


InstitutionType = Literal['Education', 'Healthcare', 'Company', 'Archive',
'Nonprofit', 'Government', 'Facility', 'Other']


class Institution(Struct):
    associated_institutions: RelatedDehydratedInstitution
    cited_by_count: int
    country_code: str
    counts_by_year: CountsByYear
    created_date: str
    display_name: str
    display_name_acronyms: list[str]
    display_name_alternatives: list[str]
    geo: Geo
    homepage_url: str
    id: str
    ids: InstitutionIds
    image_thumbnail_url: str
    image_url: str
    # international
    # repositories
    roles: list[Role]
    ror: str
    summary_stats: SummaryStats
    type: InstitutionType
    updated_date: str
    works_api_url: str
    works_count: int
    x_concepts: RatedDehydratedConcept


class APCPrice(Struct):
    currency: str
    price: int


class SourceIds(Struct):
    fatcat: str
    issn: list[str]
    issn_l: str
    mag: int
    openalex: str
    wikidata: str


class Society(Struct):
    url: str
    organization: str


SourceType = Literal['journal', 'repository', 'conference', 'ebook platform']


class DehydratedSource(Struct):
    display_name: str
    host_organization: str
    host_organization_lineage: list[str]
    host_organization_name: str
    id: str
    is_in_doaj: bool
    is_oa: bool
    issn: str
    issn_l: str
    type: SourceType


class Source(Struct):
    abbreviated_title: str
    alternate_titles: list[str]
    apc_prices: list[APCPrice]
    apc_usd: int
    cited_by_count: int
    country_code: str
    counts_by_year: CountsByYear
    created_date: str
    display_name: str
    homepage_url: str
    host_organization: str
    host_organization_lineage: list[str]
    host_organization_name: str
    id: str
    ids: SourceIds
    is_in_doaj: bool
    is_oa: bool
    issn: str
    issn_l: str
    societies: list[Society]
    summary_stats: SummaryStats
    type: SourceType
    updated_date: str
    works_api_url: str
    works_count: int
    x_concepts: list[RatedDehydratedConcept]


class AuthorIds(Struct):
    mag: int
    openalex: str
    orcid: str
    scopus: str
    twitter: str
    wikipedia: str


class DehydratedAuthor(Struct):
    display_name: str | None = None
    id: str | None = None
    orcid: str | None = None


class Author(Struct):
    cited_by_count: int
    counts_by_year: CountsByYear
    created_date: str
    display_name: str
    display_name_alternatives: list[str]
    id: str
    ids: AuthorIds
    last_known_institution: list[DehydratedInstitution]
    orcid: str
    summary_stats: SummaryStats
    updated_date: str
    works_api_url: str
    works_count: int
    x_concepts: RatedDehydratedConcept


class Location(Struct, omit_defaults=True, kw_only=True):
    is_oa: bool
    landing_page_url: str | None = None
    license: str | None = None
    source: DehydratedSource | None = None
    pdf_url: str | None = None
    version: str | None = None


class Authorship(Struct):
    author: DehydratedAuthor
    author_position: str
    institutions: list[DehydratedInstitution]
    is_corresponding: bool
    raw_affiliation_string: str


class CitationsByYear(Struct):
    year: int
    cited_by_count: int


class InvertedAbstract(Struct):
    IndexLength: int
    InvertedIndex: dict[str, list[int]]


class WorkIds(Struct):
    doi: str | None = None  # redundant with Work.doi
    mag: int | None = None
    openalex: str  # redundant with Work.id
    pmid: str | None = None
    pmcid: str | None = None


class Biblio(Struct):
    volume: str | None = None
    issue: str | None = None
    first_page: str | None = None
    last_page: str | None = None


class APC(Struct):
    value: int
    currency: str
    value_usd: int
    provenance: str


class Grant(Struct):
    funder: str
    funder_display_name: str
    award_id: str


class Mesh(Struct):
    descriptor_ui: str
    descriptor_name: str
    qualifier_ui: str
    qualifier_name: str
    is_major_topic: bool


OAStatus = Literal['gold', 'green', 'hybrid', 'bronze', 'closed']


class OpenAccess(Struct):
    oa_status: OAStatus
    oa_url: str
    any_repository_has_fulltext: bool
    is_oa: str


class Work(Struct, kw_only=True, omit_defaults=True):
    abstract_inverted_index: str | None = None
    authorships: list[Authorship]
    apc_list: list[APC]
    apc_paid: APC
    best_oa_location: Location
    biblio: Biblio
    cited_by_api_url: str
    cited_by_count: int
    concepts: list[RatedDehydratedConcept]
    corresponding_author_ids: list[str]
    corresponding_institution_ids: list[str]
    counts_by_year: list[CitationsByYear]
    created_date: str
    display_name: str | None = None
    doi: str | None = None
    grants: list[Grant]
    # //host_venue  # deprecated
    id: str
    ids: WorkIds
    is_oa: bool | None = None
    is_paratext: bool
    is_retracted: bool
    language: str | None = None
    license: str
    locations: list[Location]
    locations_count: int
    mesh: list[Mesh]
    ngrams_url: str
    open_access: OpenAccess
    primary_location: Location
    publication_date: str | None = None
    publication_year: int | None = None
    referenced_works: list[str]
    related_works: list[str]
    title: str | None = None
    type: str
    type_crossref: str
    updated_date: str | None = None
    # ngram
