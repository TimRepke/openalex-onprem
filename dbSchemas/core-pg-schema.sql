CREATE SCHEMA IF NOT EXISTS core AUTHORIZATION joe;

SET default_tablespace = '';
SET default_table_access_method = heap;

CREATE TABLE IF NOT EXISTS core.works (
    core_id text NOT NULL,
    doi text,
    mag_id text,
  	issn text,
    oai text,
    identifiers jsonb,
    title text,
  	abstract text,
    work_language jsonb,
    full_text_available bool,
    authors jsonb,
    contributors jsonb,
  	publisher text,
  	publisher_journals jsonb,
  	provider_id text,
    publication_year integer,
    publication_date text,
    work_topics jsonb,
    work_evaluation jsonb,
    work_enrichments jsonb,
    work_relations jsonb,
    work_urls jsonb,
    full_text_url text,
    PRIMARY KEY (core_id)
);

COMMENT ON TABLE core.works
IS 'Base table for core database';