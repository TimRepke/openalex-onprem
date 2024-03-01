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

--
-- Name: openalex; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA openalex;


SET default_tablespace = '';

SET default_table_access_method = heap;

CREATE TABLE openalex.authors
(
    author_id                 text NOT NULL,
    cited_by_count            integer,
    works_count               integer,
    h_index                   integer,
    i10_index                 integer,
    display_name              text,
    display_name_alternatives text,
    id_mag                    bigint,
    id_orcid                  text,
    id_scopus                 text,
    id_twitter                text,
    id_wikipedia              text,
    created_date              timestamp without time zone,
    updated_date              timestamp without time zone
--  PRIMARY KEY (author_id)
);

CREATE TABLE openalex.institutions
(
    institution_id            text NOT NULL,
    type                      text,
    homepage_url              text,
    cited_by_count            integer,
    works_count               integer,
    h_index                   integer,
    i10_index                 integer,
    display_name              text,
    display_name_alternatives text[],
    display_name_acronyms     text[],
    id_ror                    text,
    id_mag                    bigint,
    id_wikipedia              text,
    id_wikidata               text,
    id_grid                   text,
    city                      text,
    geonames_city_id          text,
    region                    text,
    country                   text,
    country_code              text,
    latitude                  real,
    longitude                 real,
    created_date              timestamp without time zone,
    updated_date              timestamp without time zone
--  PRIMARY KEY (institution_id)
);
CREATE TABLE openalex.institutions_associations
(
    parent_institution_id text NOT NULL,
    child_institution_id  text NOT NULL,
    relationship          text
--  PRIMARY KEY (parent_institution_id, child_institution_id)
);
CREATE TABLE openalex.institutions_concepts
(
    institution_id text NOT NULL,
    concept_id     text NOT NULL,
    score          real
--  PRIMARY KEY (institution_id, concept_id)
);

CREATE TABLE openalex.publishers
(
    publisher_id     text NOT NULL,
    cited_by_count   integer,
    works_count      integer,
    h_index          integer,
    i10_index        integer,
    display_name     text,
    alternate_titles text[],
    country_codes    text[],
    id_ror           text,
    id_wikidata      text,
    hierarchy_level  integer,
    lineage          text[],
    parent           text,
    created_date     timestamp without time zone,
    updated_date     timestamp without time zone
--  PRIMARY KEY (publisher_id)
);

CREATE TABLE openalex.funders
(
    funder_id        text NOT NULL,
    cited_by_count   integer,
    works_count      integer,
    h_index          integer,
    i10_index        integer,
    display_name     text,
    alternate_titles text[],
    description      text,
    homepage_url     text,
    id_ror           text,
    id_wikidata      text,
    id_crossref      text,
    id_doi           text,
    created_date     timestamp without time zone,
    updated_date     timestamp without time zone
--  PRIMARY KEY (funder_id)
);

CREATE TABLE openalex.concepts
(
    concept_id     text NOT NULL,
    cited_by_count integer,
    works_count    integer,
    h_index        integer,
    i10_index      integer,
    display_name   text,
    description    text,
    level          integer,
    id_mag         bigint,
    id_umls_cui    text[],
    id_umls_aui    text[],
    id_wikidata    text,
    id_wikipedia   text,
    created_date   timestamp without time zone,
    updated_date   timestamp without time zone
--  PRIMARY KEY (concept_id)
);
CREATE TABLE openalex.topics
(
    topic_id       text NOT NULL,
    id_wikipedia   text,
    display_name   text,
    description    text,
    keywords       text[],
    subfield_id    integer,
    subfield       text,
    field_id       integer,
    field          text,
    domain_id      integer,
    domain         text,
    works_count    integer,
    cited_by_count integer,
    created_date   timestamp without time zone,
    updated_date   timestamp without time zone
--  PRIMARY KEY (topic_id)
);
CREATE TABLE openalex.concepts_ancestors
(
    parent_concept_id text NOT NULL,
    child_concept_id  text NOT NULL
--  PRIMARY KEY (parent_concept_id, child_concept_id)
);
CREATE TABLE openalex.concepts_related
(
    concept_a_id text NOT NULL,
    concept_b_id text NOT NULL,
    score        real
--  PRIMARY KEY (concept_a_id, concept_b_id)
);

CREATE TABLE openalex.sources
(
    source_id                 text NOT NULL,
    cited_by_count            integer,
    works_count               integer,
    h_index                   integer,
    i10_index                 integer,
    display_name              text,
    abbreviated_title         text,
    alternate_titles          text[],
    country_code              text,
    homepage_url              text,
    type                      text,
    apc_usd                   integer,
    host_organization         text,
    host_organization_name    text,
    host_organization_lineage text[],
    societies                 text[],
    is_in_doaj                boolean,
    is_oa                     boolean,
    id_mag                    bigint,
    id_fatcat                 text,
    id_issn_l                 text,
    id_issn                   text[],
    id_wikidata               text,
    created_date              timestamp without time zone,
    updated_date              timestamp without time zone
--  PRIMARY KEY (source_id)
);


CREATE TABLE openalex.works
(
    work_id                        text NOT NULL,
    title                          text,
    abstract                       text,
    countries_distinct_count       integer,
    display_name                   text,
    language                       text,
    publication_date               text,
    publication_year               integer,
    volume                         text,
    issue                          text,
    first_page                     text,
    last_page                      text,
    primary_location               text,
    type                           text,
    type_crossref                  text,
    id_doi                         text,
    id_mag                         bigint,
    id_pmid                        text,
    id_pmcid                       text,
    is_oa                          boolean,
    oa_status                      text,
    oa_url                         text,
    oa_any_repository_has_fulltext boolean,
    apc_paid                       integer,
    apc_list                       integer,
    license                        text,
    cited_by_count                 integer,
    is_paratext                    boolean,
    is_retracted                   boolean,
    fulltext_origin                text,
    has_fulltext                   boolean,
    indexed_in                     text[],
    institutions_distinct_count    integer,
    is_authors_truncated           boolean,
    mesh                           json,
    grants                         json,
    created_date                   timestamp without time zone,
    updated_date                   timestamp without time zone
--  PRIMARY KEY (work_id)
);
CREATE TABLE openalex.works_authorships
(
    work_id                 text NOT NULL,
    author_id               text, -- this should never be null, but some are
    countries               text[],
    position                text,
    exact_position          int,
    raw_affiliation         text,
    raw_author_name         text,
    raw_affiliation_strings text[],
    is_corresponding        boolean
--  PRIMARY KEY (work_id, author_id)
);
CREATE TABLE openalex.works_authorship_institutions
(
    work_id        text NOT NULL,
    author_id      text NOT NULL,
    institution_id text NOT NULL
--  PRIMARY KEY (work_id, author_id, institution_id)
);
CREATE TABLE openalex.works_locations
(
    work_id          text NOT NULL,
    source_id        text, -- this should never be null, but some are
    is_oa            boolean,
    is_primary       boolean,
    is_accepted      boolean,
    is_published     boolean,
    landing_page_url text,
    license          text,
    pdf_url          text,
    version          text
--  PRIMARY KEY (work_id, source_id)
);
CREATE TABLE openalex.works_concepts
(
    work_id    text NOT NULL,
    concept_id text NOT NULL,
    score      real
--  PRIMARY KEY (work_id, concept_id)  -- unfortunately, some are not unique as promised
);
CREATE TABLE openalex.works_sdgs
(
    work_id      text NOT NULL,
    sdg_id       text NOT NULL,
    display_name text,
    score        real
--  PRIMARY KEY (work_id, sdg_id) -- unfortunately, some are not unique as promised
);
CREATE TABLE openalex.works_references
(
    src_work_id  text NOT NULL,
    trgt_work_id text NOT NULL
--  PRIMARY KEY (src_work_id, trgt_work_id) -- unfortunately, some are not unique as promised
);
CREATE TABLE openalex.works_related
(
    work_a_id text NOT NULL,
    work_b_id text NOT NULL
--  PRIMARY KEY (work_a_id, work_b_id)  -- unfortunately, some are not unique as promised
);
CREATE TABLE openalex.works_topics
(
    work_id  text NOT NULL,
    topic_id text NOT NULL,
    score    real,
    rank     int
--  PRIMARY KEY (work_a_id, work_b_id)  -- unfortunately, some are not unique as promised
);