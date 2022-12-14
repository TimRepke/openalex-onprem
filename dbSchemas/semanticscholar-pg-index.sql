
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Authors

CREATE INDEX idx_authors_name ON s2.authors USING btree (name);

-- Abstracts

CREATE INDEX idx_abstracts_abstract ON s2.abstracts USING gin (to_tsvector('english',abstract));
CREATE INDEX idx_abstracts_doi ON s2.abstracts USING btree (doi);
CREATE INDEX idx_abstracts_mag ON s2.abstracts USING btree (mag);

-- Citations

CREATE INDEX idx_citing_id ON s2.citations USING btree (citing_corpus_id);
CREATE INDEX idx_cited_id ON s2.citations USING btree (cited_corpus_id);

-- Papers

CREATE INDEX idx_papers_pubyear ON s2.papers USING btree (publication_year);
CREATE INDEX idx_papers_pubname ON s2.papers USING btree (publication_venue);
CREATE INDEX idx_papers_papername ON s2.papers USING btree (title);
CREATE INDEX idx_papers_papername_tsv ON s2.papers USING gin(to_tsvector('english',title));
CREATE INDEX idx_papers_doi ON s2.papers USING btree (doi);
CREATE INDEX idx_papers_mag ON s2.papers USING btree (mag_id);
--CREATE INDEX idx_paper_authors ON s2.papers USING gin(authors jsonb_path_ops);

-- s2orc

CREATE INDEX idx_s2orc_doi ON s2.s2orc USING btree (doi);
CREATE INDEX idx_s2orc_mag ON s2.s2orc USING btree (mag_id);
--CREATE INDEX idx_s2orc_full_text_tsv ON s2.s2orc USING gin(to_tsvector('english',full_text));

-- tldrs

CREATE INDEX idx_tldrs_summary_tsv ON s2.tldrs USING gin (to_tsvector('english',summary));