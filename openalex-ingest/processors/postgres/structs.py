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
    crossref: str | int | None = None
    doi: str | None = None


class Role(Struct, kw_only=True, omit_defaults=True):
    role: Literal['publisher', 'institution', 'funder']
    id: str | None = None
    works_count: int | None = None


class SummaryStats(Struct, kw_only=True, omit_defaults=True):
    yr_mean_citedness: float | None = None
    h_index: int | None = None
    i10_index: int | None = None


class Funder(Struct, kw_only=True, omit_defaults=True):
    alternate_titles: list[str] | None = None
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
    roles: list[Role] | None = None
    summary_stats: SummaryStats | None = None
    updated_date: str | None = None
    works_count: int | None = None


class PublisherIds(Struct, kw_only=True, omit_defaults=True):
    openalex: str | None = None
    ror: str | None = None
    wikidata: str | None = None


class ParentPublisher(Struct, kw_only=True, omit_defaults=True):
    id: str | None = None


class Publisher(Struct, kw_only=True, omit_defaults=True):
    alternate_titles: list[str] | None = None
    cited_by_count: int | None = None
    country_codes: list[str] | None = None
    counts_by_year: list[CountsByYear]
    created_date: str | None = None
    display_name: str | None = None
    hierarchy_level: int | None = None
    id: str | None = None
    ids: PublisherIds | None = None
    image_thumbnail_url: str | None = None
    image_url: str | None = None
    lineage: list[str] | None = None
    # documentation says its a string
    # parent_publisher: str | None = None
    parent_publisher: ParentPublisher | None = None
    roles: list[Role] | None = None
    sources_api_url: str | None = None
    summary_stats: SummaryStats | None = None
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
    umls_cui: list[str] | None = None
    umls_aui: list[str] | None = None
    wikidata: str | None = None
    wikipedia: str | None = None


class Concept(Struct, kw_only=True, omit_defaults=True):
    ancestors: list[DehydratedConcept] | None = None
    cited_by_count: int | None = None
    counts_by_year: list[CountsByYear]
    created_date: str | None = None
    description: str | None = None
    display_name: str | None = None
    id: str | None = None
    ids: ConceptIds | None = None
    image_thumbnail_url: str | None = None
    image_url: str | None = None
    # international
    level: int | None = None
    related_concepts: list[RatedDehydratedConcept] | None = None
    summary_stats: SummaryStats | None = None
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
    relationship: Literal['parent', 'child', 'related', 'other']


class Geo(Struct, kw_only=True, omit_defaults=True):
    city: str | None = None
    geonames_city_id: str | None = None
    region: str | None = None
    country_code: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class InstitutionIds(Struct, kw_only=True, omit_defaults=True):
    openalex: str | None = None
    ror: str | None = None
    grid: str | None = None
    wikipedia: str | None = None
    wikidata: str | None = None
    mag: int | None = None


InstitutionType = Literal['education', 'healthcare', 'company', 'archive',
'nonprofit', 'government', 'facility', 'other']


class Institution(Struct, kw_only=True, omit_defaults=True):
    associated_institutions: list[RelatedDehydratedInstitution]
    cited_by_count: int | None = None
    country_code: str | None = None
    counts_by_year: list[CountsByYear]
    created_date: str | None = None
    display_name: str | None = None
    display_name_acronyms: list[str] | None = None
    display_name_alternatives: list[str] | None = None
    geo: Geo | None = None
    homepage_url: str | None = None
    id: str | None = None
    ids: InstitutionIds | None = None
    image_thumbnail_url: str | None = None
    image_url: str | None = None
    # international
    # repositories
    roles: list[Role] | None = None
    ror: str | None = None
    summary_stats: SummaryStats | None = None
    type: InstitutionType | None = None
    updated_date: str | None = None
    works_api_url: str | None = None
    works_count: int | None = None
    x_concepts: list[RatedDehydratedConcept] | None = None


class APCPrice(Struct, kw_only=True, omit_defaults=True):
    currency: str | None = None
    price: int | None = None


class SourceIds(Struct, kw_only=True, omit_defaults=True):
    fatcat: str | None = None
    issn: list[str] | None = None
    issn_l: str | None = None
    mag: int | None = None
    openalex: str | None = None
    wikidata: str | None = None


class Society(Struct, kw_only=True, omit_defaults=True):
    url: str | None = None
    organization: str | None = None


SourceType = Literal['journal', 'repository', 'conference', 'ebook platform', 'book series', 'other']


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
    alternate_titles: list[str] | None = None
    apc_prices: list[APCPrice] | None = None
    apc_usd: int | None = None
    cited_by_count: int | None = None
    country_code: str | None = None
    counts_by_year: list[CountsByYear] | None = None
    created_date: str | None = None
    display_name: str | None = None
    homepage_url: str | None = None
    host_organization: str | None = None
    host_organization_lineage: list[str] | None = None
    host_organization_name: str | None = None
    id: str | None = None
    ids: SourceIds | None = None
    is_in_doaj: bool | None = None
    is_oa: bool | None = None
    issn: list[str] | None = None
    issn_l: str | None = None
    societies: list[Society] | None = None
    summary_stats: SummaryStats | None = None
    type: SourceType | None = None
    updated_date: str | None = None
    works_api_url: str | None = None
    works_count: int | None = None
    x_concepts: list[RatedDehydratedConcept] | None = None


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


class Affiliation(Struct, kw_only=True, omit_defaults=True):
    institution: DehydratedInstitution | None = None
    years: list[int] | None = None


class Author(Struct, kw_only=True, omit_defaults=True):
    # affiliations: list[Affiliation] | None = None  # TODO use this
    cited_by_count: int | None = None
    counts_by_year: list[CountsByYear] | None = None
    created_date: str | None = None
    display_name: str | None = None
    display_name_alternatives: list[str] | None = None
    id: str | None = None
    ids: AuthorIds | None = None
    last_known_institution: DehydratedInstitution | None = None
    # last_known_institutions: DehydratedInstitution | None = None
    orcid: str | None = None
    summary_stats: SummaryStats | None = None
    updated_date: str | None = None
    works_api_url: str | None = None
    works_count: int | None = None
    x_concepts: list[RatedDehydratedConcept] | None = None


class Location(Struct, omit_defaults=True, kw_only=True):
    is_accepted: bool | None = None
    is_oa: bool | None = None
    is_published: bool | None = None
    landing_page_url: str | None = None
    license: str | None = None
    pdf_url: str | None = None
    source: DehydratedSource | None = None
    version: str | None = None


class Authorship(Struct, kw_only=True, omit_defaults=True):
    author: DehydratedAuthor
    author_position: str | None = None
    countries: list[str] | None = None
    institutions: list[DehydratedInstitution] | None = None
    is_corresponding: bool | None = None
    raw_affiliation_string: str | None = None
    raw_affiliation_strings: list[str] | None = None
    raw_author_name: str | None = None


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
    is_oa: bool | None = None


class SustainableDevelopmentGoal(Struct, kw_only=True, omit_defaults=True):
    id: str | None = None
    display_name: str | None = None
    score: float | None = None


class TopicHierarchy(Struct, omit_defaults=True, kw_only=True):
    id: str | None = None
    display_name: str | None = None


class TopicIds(Struct, omit_defaults=True, kw_only=True):
    id: str | None = None
    wikipedia: str | None = None


class Topic(Struct, omit_defaults=True, kw_only=True):
    id: str | None = None
    ids: TopicIds | None = None
    display_name: str | None = None
    description: str | None = None
    keywords: list[str] | None = None
    subfield: TopicHierarchy | None = None
    field: TopicHierarchy | None = None
    domain: TopicHierarchy | None = None
    works_count: int | None = None
    cited_by_count: int | None = None
    updated_date: str | None = None
    created_date: str | None = None


class DehydratedTopic(Struct, omit_defaults=True, kw_only=True):
    id: str | None = None
    display_name: str | None = None
    score: float | None = None
    subfield: TopicHierarchy | None = None
    field: TopicHierarchy | None = None
    domain: TopicHierarchy | None = None


class Work(Struct, kw_only=True, omit_defaults=True):
    abstract_inverted_index: dict[str, list[int]] | None = None
    authorships: list[Authorship] | None = None
    apc_list: APC | None = None
    apc_paid: APC | list[APC] | None = None
    best_oa_location: Location | None = None
    biblio: Biblio | None = None
    cited_by_api_url: str | None = None
    cited_by_count: int | None = None
    concepts: list[RatedDehydratedConcept] | None = None
    corresponding_author_ids: list[str] | None = None
    corresponding_institution_ids: list[str] | None = None
    countries_distinct_count: int | None = None
    counts_by_year: list[CitationsByYear] | None = None
    created_date: str | None = None
    display_name: str | None = None
    doi: str | None = None
    fulltext_origin: str | None = None
    grants: list[Grant] | None = None
    has_fulltext: bool | None = None
    id: str | None = None
    ids: WorkIds | None = None
    indexed_in: list[str] | None = None
    institutions_distinct_count: int | None = None
    is_authors_truncated: bool | None = None
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
    sustainable_development_goals: list[SustainableDevelopmentGoal] | None = None
    title: str | None = None
    topics: list[DehydratedTopic] | None = None
    type: str | None = None
    type_crossref: str | None = None
    updated_date: str | None = None
