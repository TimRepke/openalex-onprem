CREATE SCHEMA IF NOT EXISTS s2 AUTHORIZATION joe;

CREATE EXTENSION pg_trgm;
CREATE EXTENSION btree_gin;

SET default_tablespace = '';
SET default_table_access_method = heap;

CREATE TABLE s2.authors (
	author_id text NOT NULL,
	external_ids jsonb,
	name text,
	aliases jsonb,
	url text,
    homepage text,
	affiliations jsonb,
	paper_count integer,
	citation_count integer,
	hindex integer,
	updated_date timestamp without time zone,
	PRIMARY KEY (author_id)
);

COMMENT ON TABLE s2.authors
IS 'Provides summary information about authors';

CREATE TABLE s2.abstracts (
	corpus_id text NOT NULL,
    doi text,
    mag_id text,
    abstract text,
    open_access_status text,
    open_access_license text,
    open_access_url text,
    external_ids jsonb,
	updated_date timestamp without time zone,
	PRIMARY KEY (corpus_id)
);

COMMENT ON TABLE s2.abstracts
IS 'provides abstract text for selected papers';

CREATE TABLE s2.citations (
	citation_id SERIAL NOT NULL,
	citing_corpus_id text NOT NULL,
	cited_corpus_id text,
	is_influential boolean, -- s2 evaluation of the "importance" of the citation to the citing corpus
	contexts jsonb, -- Text surrounding the citation in the source paper's body
	intents jsonb, -- Classification of the intent behind the citations.
	updated_date timestamp without time zone,
	PRIMARY KEY (citation_id)
);

COMMENT ON TABLE s2.citations
IS 'provides details about the relationship between citing and cited corpus ids.';

CREATE TABLE IF NOT EXISTS s2.papers (
  corpus_id text NOT NULL,
  doi text,
  mag_id text,
  external_ids jsonb,
  title text,
  publication_year int,
  publication_venue text,
  authors jsonb,
  is_open_access bool,
  url text,
  s2_fields_of_study jsonb,
  citation_count int,
  reference_count int,
  influential_citation_count int,
  updated_date timestamp without time zone,
  PRIMARY KEY (corpus_id)
);

COMMENT ON TABLE s2.papers
IS 'provides core metadata about papers. For abstract or citation information join corpus_id on the relevant tables';

CREATE TABLE IF NOT EXISTS s2.s2orc (
    corpus_id text NOT NULL,
    doi text,
    mag_id text,
    external_ids jsonb,
    open_access_metadata jsonb,
    full_text text,
    annotations jsonb,
    updated_date timestamp without time zone,
    PRIMARY KEY (corpus_id)
    );

COMMENT ON TABLE s2.s2orc
IS 'Available full text contents for semantic scholar documents';

CREATE TABLE IF NOT EXISTS  s2.tldrs (
	corpus_id text NOT NULL,
	model text,
	summary text,
	PRIMARY KEY (corpus_id)
);

COMMENT ON TABLE s2.tldrs
IS 'semantic scholar auto-generated natural-language summaries of paper content using SciTLDR model available at https://github.com/allenai/scitldr';

