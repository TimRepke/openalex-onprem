from typing import Literal
from msgspec import Struct


class CountsByYear(Struct, kw_only=True, omit_defaults=True):
    year: int | None = None
    works_count: int | None = None
    cited_by_count: int | None = None


class FunderIds(Struct, kw_only=True, omit_defaults=True):
    openalex: str | None = None
    ror: str | None = None
    wikidata: str | None = None
    crossref: str | None = None
    doi: str | None = None


class Role(Struct, kw_only=True, omit_defaults=True):
    role: Literal['publisher', 'institution', 'funder']
    id: str | None = None
    works_count: int | None = None


class SummaryStats(Struct, kw_only=True, omit_defaults=True):
    yr_mean_citedness: float
    h_index: int | None = None
    i10_index: int | None = None


class Funder(Struct, kw_only=True, omit_defaults=True):
    alternate_titles: list[str]
    cited_by_count: int | None = None
    country_code: str | None = None
    counts_by_year: list[CountsByYear]
    created_date: str | None = None
    description: str | None = None
    display_name: str | None = None
    grants_count: int | None = None
    homepage_url: str | None = None
    id: str | None = None
    ids: FunderIds
    image_thumbnail_url: str | None = None
    image_url: str | None = None
    roles: list[Role]
    summary_stats: SummaryStats
    updated_date: str | None = None
    works_count: int | None = None


class PublisherIds(Struct, kw_only=True, omit_defaults=True):
    openalex: str | None = None
    ror: str | None = None
    wikidata: str | None = None


class Publisher(Struct, kw_only=True, omit_defaults=True):
    alternate_titles: list[str]
    cited_by_count: int | None = None
    country_codes: list[str]
    counts_by_year: list[CountsByYear]
    created_date: str | None = None
    display_name: str | None = None
    hierarchy_level: int | None = None
    id: str | None = None
    ids: PublisherIds
    image_thumbnail_url: str | None = None
    image_url: str | None = None
    lineage: list[str]
    parent_publisher: str | None = None
    roles: list[Role]
    sources_api_url: str | None = None
    summary_stats: SummaryStats
    updated_date: str | None = None
    works_count: int | None = None


class DehydratedConcept(Struct, kw_only=True, omit_defaults=True):
    display_name: str | None = None
    id: str | None = None
    level: int | None = None
    wikidata: str | None = None


class RatedDehydratedConcept(Struct, kw_only=True, omit_defaults=True):
    display_name: str | None = None
    id: str | None = None
    level: int | None = None
    wikidata: str | None = None
    score: float


class ConceptIds(Struct, kw_only=True, omit_defaults=True):
    mag: int | None = None
    openalex: str | None = None
    umls_cui: list[str]
    umls_aui: list[str]
    wikidata: str | None = None
    wikipedia: str | None = None


class Concept(Struct, kw_only=True, omit_defaults=True):
    ancestors: list[DehydratedConcept]
    cited_by_count: int | None = None
    counts_by_year: list[CountsByYear]
    created_date: str | None = None
    description: str | None = None
    display_name: str | None = None
    id: str | None = None
    ids: ConceptIds
    image_thumbnail_url: str | None = None
    image_url: str | None = None
    # international
    level: int | None = None
    related_concepts: list[RatedDehydratedConcept]
    summary_stats: SummaryStats
    updated_date: str | None = None
    wikidata: str | None = None
    works_api_url: str | None = None
    works_count: int | None = None


class DehydratedInstitution(Struct, kw_only=True, omit_defaults=True):
    country_code: str | None = None
    display_name: str | None = None
    id: str | None = None
    ror: str | None = None
    type: str | None = None


class RelatedDehydratedInstitution(Struct, kw_only=True, omit_defaults=True):
    country_code: str | None = None
    display_name: str | None = None
    id: str | None = None
    ror: str | None = None
    type: str | None = None
    relationship: Literal['parent', 'child', 'related']


class Geo(Struct, kw_only=True, omit_defaults=True):
    city: str | None = None
    geonames_city_id: str | None = None
    region: str | None = None
    country_code: str | None = None
    country: str | None = None
    latitude: float
    longitude: float


class InstitutionIds(Struct, kw_only=True, omit_defaults=True):
    openalex: str | None = None
    ror: str | None = None
    grid: str | None = None
    wikipedia: str | None = None
    wikidata: str | None = None
    mag: int | None = None


InstitutionType = Literal['Education', 'Healthcare', 'Company', 'Archive',
'Nonprofit', 'Government', 'Facility', 'Other']


class Institution(Struct, kw_only=True, omit_defaults=True):
    associated_institutions: list[RelatedDehydratedInstitution]
    cited_by_count: int | None = None
    country_code: str | None = None
    counts_by_year: list[CountsByYear]
    created_date: str | None = None
    display_name: str | None = None
    display_name_acronyms: list[str]
    display_name_alternatives: list[str]
    geo: Geo
    homepage_url: str | None = None
    id: str | None = None
    ids: InstitutionIds
    image_thumbnail_url: str | None = None
    image_url: str | None = None
    # international
    # repositories
    roles: list[Role]
    ror: str | None = None
    summary_stats: SummaryStats
    type: InstitutionType | None = None
    updated_date: str | None = None
    works_api_url: str | None = None
    works_count: int | None = None
    x_concepts: list[RatedDehydratedConcept]


class APCPrice(Struct, kw_only=True, omit_defaults=True):
    currency: str | None = None
    price: int | None = None


class SourceIds(Struct, kw_only=True, omit_defaults=True):
    fatcat: str | None = None
    issn: list[str]
    issn_l: str | None = None
    mag: int | None = None
    openalex: str | None = None
    wikidata: str | None = None


class Society(Struct, kw_only=True, omit_defaults=True):
    url: str | None = None
    organization: str | None = None


SourceType = Literal['journal', 'repository', 'conference', 'ebook platform']


class DehydratedSource(Struct, kw_only=True, omit_defaults=True):
    display_name: str | None = None
    host_organization: str | None = None
    host_organization_lineage: list[str] | None = None
    host_organization_name: str | None = None
    id: str | None = None
    is_in_doaj: bool | None = None
    is_oa: bool | None = None
    issn: list[str] | None = None
    issn_l: str | None = None
    type: SourceType | None = None


class Source(Struct, kw_only=True, omit_defaults=True):
    abbreviated_title: str | None = None
    alternate_titles: list[str]
    apc_prices: list[APCPrice]
    apc_usd: int | None = None
    cited_by_count: int | None = None
    country_code: str | None = None
    counts_by_year: list[CountsByYear]
    created_date: str | None = None
    display_name: str | None = None
    homepage_url: str | None = None
    host_organization: str | None = None
    host_organization_lineage: list[str]
    host_organization_name: str | None = None
    id: str | None = None
    ids: SourceIds
    is_in_doaj: bool | None = None
    is_oa: bool | None = None
    issn: list[str]
    issn_l: str | None = None
    societies: list[Society]
    summary_stats: SummaryStats
    type: SourceType
    updated_date: str | None = None
    works_api_url: str | None = None
    works_count: int | None = None
    x_concepts: list[RatedDehydratedConcept]


class AuthorIds(Struct, kw_only=True, omit_defaults=True):
    mag: int | None = None
    openalex: str | None = None
    orcid: str | None = None
    scopus: str | None = None
    twitter: str | None = None
    wikipedia: str | None = None


class DehydratedAuthor(Struct, kw_only=True, omit_defaults=True):
    display_name: str | None = None
    id: str | None = None
    orcid: str | None = None


class Author(Struct, kw_only=True, omit_defaults=True):
    cited_by_count: int | None = None
    counts_by_year: list[CountsByYear]
    created_date: str | None = None
    display_name: str | None = None
    display_name_alternatives: list[str]
    id: str | None = None
    ids: AuthorIds
    last_known_institution: list[DehydratedInstitution]
    orcid: str | None = None
    summary_stats: SummaryStats
    updated_date: str | None = None
    works_api_url: str | None = None
    works_count: int | None = None
    x_concepts: RatedDehydratedConcept


class Location(Struct, omit_defaults=True, kw_only=True):
    is_oa: bool | None = None
    landing_page_url: str | None = None
    license: str | None = None
    source: DehydratedSource | None = None
    pdf_url: str | None = None
    version: str | None = None


class Authorship(Struct, kw_only=True, omit_defaults=True):
    author: DehydratedAuthor
    author_position: str | None = None
    institutions: list[DehydratedInstitution] | None = None
    is_corresponding: bool | None = None
    raw_affiliation_string: str | None = None


class CitationsByYear(Struct, kw_only=True, omit_defaults=True):
    year: int | None = None
    cited_by_count: int | None = None


class InvertedAbstract(Struct, kw_only=True, omit_defaults=True):
    IndexLength: int | None = None
    InvertedIndex: dict[str, list[int]]


class WorkIds(Struct, kw_only=True, omit_defaults=True):
    doi: str | None = None  # redundant with Work.doi
    mag: int | None = None
    openalex: str  # redundant with Work.id
    pmid: str | None = None
    pmcid: str | None = None


class Biblio(Struct, kw_only=True, omit_defaults=True):
    volume: str | None = None
    issue: str | None = None
    first_page: str | None = None
    last_page: str | None = None


class APC(Struct, kw_only=True, omit_defaults=True):
    value: int | None = None
    currency: str | None = None
    value_usd: int | None = None
    provenance: str | None = None


class Grant(Struct, kw_only=True, omit_defaults=True):
    funder: str | None = None
    funder_display_name: str | None = None
    award_id: str | None = None


class Mesh(Struct, kw_only=True, omit_defaults=True):
    descriptor_ui: str | None = None
    descriptor_name: str | None = None
    qualifier_ui: str | None = None
    qualifier_name: str | None = None
    is_major_topic: bool | None = None


OAStatus = Literal['gold', 'green', 'hybrid', 'bronze', 'closed']


class OpenAccess(Struct, kw_only=True, omit_defaults=True):
    oa_status: OAStatus | None = None
    oa_url: str | None = None
    any_repository_has_fulltext: bool | None = None
    is_oa: str | None = None


class Work(Struct, kw_only=True, omit_defaults=True):
    abstract_inverted_index: str | None = None
    authorships: list[Authorship]
    apc_list: list[APC] | None = None
    apc_paid: APC | None = None
    best_oa_location: Location | None = None
    biblio: Biblio | None = None
    cited_by_api_url: str | None = None
    cited_by_count: int | None = None
    concepts: list[RatedDehydratedConcept] | None = None
    corresponding_author_ids: list[str] | None = None
    corresponding_institution_ids: list[str] | None = None
    counts_by_year: list[CitationsByYear] | None = None
    created_date: str | None = None
    display_name: str | None = None
    doi: str | None = None
    grants: list[Grant] | None = None
    id: str | None = None
    ids: WorkIds | None = None
    is_oa: bool | None = None
    is_paratext: bool | None = None
    is_retracted: bool | None = None
    language: str | None = None
    license: str | None = None
    locations: list[Location] | None = None
    locations_count: int | None = None
    mesh: list[Mesh] | None = None
    open_access: OpenAccess | None = None
    primary_location: Location | None = None
    publication_date: str | None = None
    publication_year: int | None = None
    referenced_works: list[str] | None = None
    related_works: list[str] | None = None
    title: str | None = None
    type: str | None = None
    type_crossref: str | None = None
    updated_date: str | None = None
    # //host_venue  # deprecated
    # ngram
    # ngrams_url: str | None = None
