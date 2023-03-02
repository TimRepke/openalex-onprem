
-- Default settings given by openalex in original script

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

CREATE SCHEMA IF NOT EXISTS openalex;

SET default_tablespace = '';
SET default_table_access_method = heap;

-- AUTHORS TABLES

CREATE TABLE IF NOT EXISTS openalex.authors (
    id text NOT NULL,
    orcid text, -- canonical external id
    display_name text,
    display_name_alternatives json,
    works_count integer,
    cited_by_count integer,
    last_known_institution text,
    updated_date timestamp without time zone,
    PRIMARY KEY (id)
);

COMMENT ON TABLE openalex.authors
IS 'provides summary information about authors. linked to works via works_authorships';

CREATE TABLE IF NOT EXISTS openalex.authors_counts_by_year (
    author_id text NOT NULL,
    year integer NOT NULL,
    works_count integer,
    cited_by_count integer,
    PRIMARY KEY (author_id, year)
);

COMMENT ON TABLE openalex.authors_counts_by_year
IS 'yearly aggregate statistics on authors';

CREATE TABLE IF NOT EXISTS openalex.authors_ids (
    author_id text NOT NULL,
    openalex text,
    orcid text, -- canonical external id
    scopus text,
    twitter text,
    wikipedia text,
    mag bigint,
    PRIMARY KEY (author_id)
);

COMMENT ON TABLE openalex.authors_ids
IS 'contains external ids for authors';

-- CONCEPTS TABLES

CREATE TABLE IF NOT EXISTS openalex.concepts (
    id text NOT NULL,
    wikidata text,
    display_name text,
    level integer,
    description text,
    works_count integer,
    cited_by_count integer,
    updated_date timestamp without time zone,
    PRIMARY KEY (id)
);

COMMENT ON TABLE openalex.concepts
IS 'primary table for concepts. abstracted topics which are assigned to works and related hierarchically. for more modeling info please see https://github.com/ourresearch/openalex-concept-tagging';

CREATE TABLE IF NOT EXISTS openalex.concepts_ancestors (
    concept_id text,
    ancestor_id text,
    PRIMARY KEY (concept_id, ancestor_id)
);

COMMENT ON TABLE openalex.concepts_ancestors
IS 'relationship table for concepts and their hierarchical ancestors';

CREATE TABLE IF NOT EXISTS openalex.concepts_counts_by_year (
    concept_id text NOT NULL,
    year integer NOT NULL,
    works_count integer,
    cited_by_count integer,
    PRIMARY KEY (concept_id, year)
);

COMMENT ON TABLE openalex.concepts_counts_by_year
IS 'yearly aggregate statistics on concepts';

CREATE TABLE IF NOT EXISTS openalex.concepts_ids (
    concept_id text NOT NULL,
    openalex text,
    wikidata text,
    wikipedia text,
    umls_aui json,
    umls_cui json,
    mag bigint,
    PRIMARY KEY (concept_id)
);

COMMENT ON TABLE openalex.concepts_ids
IS 'contains external ids for concepts';

CREATE TABLE IF NOT EXISTS openalex.concepts_related_concepts (
    concept_id text,
    related_concept_id text,
    score real, -- openalex model likeness score
    PRIMARY KEY (concept_id, related_concept_id)
);

COMMENT ON TABLE openalex.concepts_related_concepts
IS 'horizontal relationship between concepts';

-- INSTITUTIONS TABLES

CREATE TABLE IF NOT EXISTS openalex.institutions (
    id text NOT NULL,
    ror text, -- canonical external id
    display_name text,
    type text,
    country_code text,
    homepage_url text,
    image_url text,
    image_thumbnail_url text,
    display_name_acroynyms json,
    display_name_alternatives json,
    works_count integer,
    cited_by_count integer,
    updated_date timestamp without time zone,
    PRIMARY KEY (id)
);

COMMENT ON TABLE openalex.institutions
IS 'institutions are organizations to which authors claim affiliations. linked to works via works_authorships.';

CREATE TABLE IF NOT EXISTS openalex.institutions_associated_institutions (
    institution_id text,
    associated_institution_id text,
    relationship text,
    PRIMARY KEY (institution_id, associated_institution_id)
);

COMMENT ON TABLE openalex.institutions_associated_institutions
IS 'relationship table between institutions';

CREATE TABLE IF NOT EXISTS openalex.institutions_counts_by_year (
    institution_id text NOT NULL,
    year integer NOT NULL,
    works_count integer,
    cited_by_count integer,
    PRIMARY KEY (institution_id, year)
);

COMMENT ON TABLE openalex.institutions_counts_by_year
IS 'yearly aggregate statistics on institutions';

CREATE TABLE IF NOT EXISTS openalex.institutions_geo (
    institution_id text NOT NULL,
    city text,
    geonames_city_id text,
    region text,
    country_code text,
    country text,
    latitude real,
    longitude real,
    PRIMARY KEY (institution_id)
);

COMMENT ON TABLE openalex.institutions_geo
IS 'physical location of institutions';

CREATE TABLE IF NOT EXISTS openalex.institutions_ids (
    institution_id text NOT NULL,
    openalex text,
    ror text, -- canonical external id
    grid text,
    wikipedia text,
    wikidata text,
    mag bigint,
    PRIMARY KEY (institution_id)
);

COMMENT ON TABLE openalex.institutions_ids
IS 'contains external ids for institutions';

-- VENUES TABLES

CREATE TABLE IF NOT EXISTS openalex.venues (
    id text NOT NULL,
    issn_l text, -- canonical external id
    issn json,
    display_name text,
    publisher text,
    works_count integer,
    cited_by_count integer,
    is_oa boolean, -- open access
    is_in_doaj boolean, -- directory of open access journals
    homepage_url text,
    updated_date timestamp without time zone,
    PRIMARY KEY (id)
);

COMMENT ON TABLE openalex.venues
IS 'where works are hosted. information comes from crossref, issn network, and mag. linked to works via works_host_venue and works_alternate host venues.';

CREATE TABLE IF NOT EXISTS openalex.venues_counts_by_year (
    venue_id text NOT NULL,
    year integer NOT NULL,
    works_count integer,
    cited_by_count integer,
    PRIMARY KEY (venue_id, year)
);

COMMENT ON TABLE openalex.venues_counts_by_year
IS 'yearly aggregate statistics on venues';

CREATE TABLE IF NOT EXISTS openalex.venues_ids (
    venue_id text,
    openalex text,
    issn_l text,
    issn json,
    mag bigint,
    PRIMARY KEY (venue_id)
);

COMMENT ON TABLE openalex.venues_ids
IS 'contains external ids for venues';

-- WORKS TABLES

CREATE TABLE IF NOT EXISTS openalex.works (
    id text NOT NULL,
    doi text, -- canonical external id
    mag text,
    pmid text,
    pmcid text,
    title text,
    publication_year integer,
    publication_date text,
    type text,
    cited_by_count integer,
    is_retracted boolean,
    is_paratext boolean,
    is_open_access boolean,
    abstract text,
    PRIMARY KEY (id)
);

COMMENT ON TABLE openalex.works
IS 'documents like journal articles, books, datasets, and theses. sources include crossref, pubmed, institutional and discipline-specific repositories (eg, arxiv). older works come from the now-defunct microsoft academic graph. works are clustered together using fuzzy matching on publication date, title, and author list';

CREATE TABLE IF NOT EXISTS openalex.works_alternate_host_venues (
    row_id SERIAL PRIMARY KEY,
    work_id text,
    venue_id text,
    url text,
    is_oa boolean,
    version text,
    license text
--   PRIMARY KEY (work_id, venue_id)
);

COMMENT ON TABLE openalex.works_alternate_host_venues
IS 'relationship table between works and secondary venues';

CREATE TABLE IF NOT EXISTS openalex.works_authorships (
    row_id SERIAL PRIMARY KEY,
    work_id text,
    author_position text,
    author_id text,
    institution_id text,
    raw_affiliation_string text
--    PRIMARY KEY (work_id, author_id)
);

COMMENT ON TABLE openalex.works_authorships
IS 'relationship table between works and authors';

CREATE TABLE IF NOT EXISTS openalex.works_biblio (
    work_id text NOT NULL,
    volume text,
    issue text,
    first_page text,
    last_page text,
    PRIMARY KEY (work_id)
);

COMMENT ON TABLE openalex.works_biblio
IS 'biblio location information for works';

CREATE TABLE IF NOT EXISTS openalex.works_concepts (
    work_id text,
    concept_id text,
    score real,
    PRIMARY KEY (work_id, concept_id)
);

COMMENT ON TABLE openalex.works_concepts
IS 'relationship table between works and concepts. for more information on concepts see comment on concepts table.';

CREATE TABLE IF NOT EXISTS openalex.works_host_venues (
    work_id text,
    venue_id text,
    url text,
    is_oa boolean,
    version text,
    license text,
    PRIMARY KEY (work_id, venue_id)
);

COMMENT ON TABLE openalex.works_host_venues
IS 'relationship table between works and primary venue';

--CREATE TABLE IF NOT EXISTS openalex.works_ids (
--    work_id text NOT NULL,
--    openalex text,
--    doi text, -- canonical external id
--    mag bigint,
--    pmid text,
--    pmcid text,
--    PRIMARY KEY (work_id)
--);

--COMMENT ON TABLE openalex.works_ids
--IS 'contains external ids for works';

CREATE TABLE IF NOT EXISTS openalex.works_mesh (
    work_id text,
    descriptor_ui text,
    descriptor_name text,
    qualifier_ui text,
    qualifier_name text,
    is_major_topic boolean,
    PRIMARY KEY (work_id, descriptor_ui, qualifier_ui)
);

COMMENT ON TABLE openalex.works_mesh
IS 'pubmed works only. list of medical subject headings. for more information see https://www.nlm.nih.gov/mesh/meshhome.html';

CREATE TABLE IF NOT EXISTS openalex.works_open_access (
    work_id text NOT NULL,
    is_oa boolean,
    oa_status text,
    oa_url text,
    PRIMARY KEY (work_id)
);

COMMENT ON TABLE openalex.works_open_access
IS 'open access status of works';

CREATE TABLE IF NOT EXISTS openalex.works_referenced_works (
    work_id text,
    referenced_work_id text,
    PRIMARY KEY (work_id, referenced_work_id)
);

COMMENT ON TABLE openalex.works_referenced_works
IS 'relationship table between works and other works it references';
