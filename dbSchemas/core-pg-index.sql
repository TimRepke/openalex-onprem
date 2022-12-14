
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

CREATE INDEX IF NOT EXISTS idx_core_works_doi ON core.works USING btree (doi);
CREATE INDEX IF NOT EXISTS idx_core_works_issn ON core.works USING btree (issn);
CREATE INDEX IF NOT EXISTS idx_core_works_oai ON core.works USING btree (oai);

CREATE INDEX IF NOT EXISTS idx_core_works_title ON core.works USING btree (title);
CREATE INDEX IF NOT EXISTS idx_core_works_title_tsv ON core.works USING GIN (to_tsvector('english',title));
CREATE INDEX IF NOT EXISTS idx_core_works_abstract_tsv ON core.works USING GIN (to_tsvector('english',abstract));

CREATE INDEX IF NOT EXISTS idx_core_works_authors ON core.works USING GIN (authors);
CREATE INDEX IF NOT EXISTS idx_core_works_publisher ON core.works USING btree (publisher);
CREATE INDEX IF NOT EXISTS idx_core_works_provider_id ON core.works USING btree (provider_id);
CREATE INDEX IF NOT EXISTS idx_core_works_publication_year ON core.works USING btree (publication_year);

CREATE INDEX IF NOT EXISTS idx_core_works_work_topics ON core.works USING GIN (work_topics);
CREATE INDEX IF NOT EXISTS idx_core_works_work_eval ON core.works USING GIN (work_evaluation);