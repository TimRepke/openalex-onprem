CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

ALTER TABLE openalex.works
ADD COLUMN IF NOT EXISTS ts_title tsvector,
ADD COLUMN IF NOT EXISTS ts_abstract tsvector,
ADD COLUMN IF NOT EXISTS ts_ta tsvector;

--BEGIN;

DROP INDEX IF EXISTS idx_works_title_tsv;
DROP INDEX IF EXISTS idx_works_title_tri;
DROP INDEX IF EXISTS idx_works_abstract_tsv;
DROP INDEX IF EXISTS idx_works_abstract_tri;
DROP INDEX IF EXISTS idx_works_ta_tsv;

UPDATE openalex.works
SET ts_title = to_tsvector('simple',title);

UPDATE openalex.works
SET ts_abstract = to_tsvector('simple',abstract);

UPDATE openalex.works
SET ts_ta = ts_title || ts_abstract;

--COMMIT;

CREATE INDEX idx_works_title_tsv ON openalex.works USING gin (ts_title);
CREATE INDEX idx_works_title_tri ON openalex.works USING gin (title gin_trgm_ops);

CREATE INDEX idx_works_abstract_tsv ON openalex.works USING gin (ts_abstract);
CREATE INDEX idx_works_abstract_tri ON openalex.works USING gin (abstract gin_trgm_ops);

CREATE INDEX idx_works_ta_tsv ON openalex.works USING gin (ts_ta);