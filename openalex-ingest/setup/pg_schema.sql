--
-- PostgreSQL database dump
--

-- Dumped from database version 13.5 (Ubuntu 13.5-2.heroku1+1)
-- Dumped by pg_dump version 14.1

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
    id                        text NOT NULL PRIMARY KEY,
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
);

CREATE TABLE openalex.institutions
(
    id                        text NOT NULL PRIMARY KEY,
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


);
CREATE TABLE openalex.institutions_associations
(
    institution_a_id text NOT NULL,
    institution_b_id text NOT NULL,
    relationship     text,

    PRIMARY KEY (institution_a_id, institution_b_id)
);
CREATE TABLE openalex.institutions_concepts
(
    institution_id text NOT NULL,
    concept_id     text NOT NULL,
    score          real,

    PRIMARY KEY (institution_id, concept_id)
);

CREATE TABLE openalex.publishers
(
    id               text NOT NULL PRIMARY KEY,
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
);

CREATE TABLE openalex.funders
(
    id               text NOT NULL PRIMARY KEY,
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
);

CREATE TABLE openalex.concepts
(
    id             text NOT NULL PRIMARY KEY,
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
);
CREATE TABLE openalex.concepts_ancestors
(
    concept_a_id text NOT NULL,
    concept_b_id text NOT NULL,

    PRIMARY KEY (concept_a_id, concept_b_id)
);
CREATE TABLE openalex.concepts_related
(
    concept_a_id text NOT NULL,
    concept_b_id text NOT NULL,
    score        real,

    PRIMARY KEY (concept_a_id, concept_b_id)
);

CREATE TABLE openalex.sources
(
    id                        text PRIMARY KEY,
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
);


CREATE TABLE openalex.works
(
    id                             text PRIMARY KEY,
    title                          text,
    abstract                       text,
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
    mesh                           json,
    grants                         json,
    created_date                   timestamp without time zone,
    updated_date                   timestamp without time zone
);
CREATE TABLE openalex.works_authorships
(
    row_id           BIGSERIAL PRIMARY KEY,
    work_id          text NOT NULL,
    author_id        text, -- this should never be null, but some are
    position         text,
    exact_position   int,
    institutions     text[],
    raw_affiliation  text,
    is_corresponding boolean
);
CREATE TABLE openalex.works_locations
(
    row_id           BIGSERIAL PRIMARY KEY,
    work_id          text NOT NULL,
    source_id        text, -- this should never be null, but some are
    is_oa            boolean,
    is_primary       boolean,
    landing_page_url text,
    license          text,
    pdf_url          text,
    version          text
);
CREATE TABLE openalex.works_concepts
(
    work_id    text NOT NULL,
    concept_id text NOT NULL,
    score      real,

    PRIMARY KEY (work_id, concept_id)
);
CREATE TABLE openalex.works_references
(
    work_a_id text NOT NULL,
    work_b_id text NOT NULL,

    PRIMARY KEY (work_a_id, work_b_id)
);
CREATE TABLE openalex.works_related
(
    work_a_id text NOT NULL,
    work_b_id text NOT NULL,

    PRIMARY KEY (work_a_id, work_b_id)
);

CREATE INDEX works_id_doi_idx ON openalex.works USING hash (id_doi);
CREATE INDEX works_publication_year_idx ON openalex.works USING btree (id_doi);


-- old stuff for reference:
-- CREATE INDEX concepts_ancestors_concept_id_idx ON openalex.concepts_ancestors USING btree (concept_id);
--
-- CREATE INDEX concepts_related_concepts_concept_id_idx ON openalex.concepts_related_concepts USING btree (concept_id);
--
-- CREATE INDEX concepts_related_concepts_related_concept_id_idx ON openalex.concepts_related_concepts USING btree (related_concept_id);
--
-- CREATE INDEX works_primary_locations_work_id_idx ON openalex.works_primary_locations USING btree (work_id);
--
-- CREATE INDEX works_locations_work_id_idx ON openalex.works_locations USING btree (work_id);
--
-- CREATE INDEX works_best_oa_locations_work_id_idx ON openalex.works_best_oa_locations USING btree (work_id);
