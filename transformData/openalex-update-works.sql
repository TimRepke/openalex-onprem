ALTER TABLE openalex.works
ADD COLUMN IF NOT EXISTS ts_title tsvector,
ADD COLUMN IF NOT EXISTS ts_abstract tsvector,
ADD COLUMN IF NOT EXISTS ts_ta tsvector;

BEGIN;

DROP INDEX IF EXISTS idx_works_title_tsv;
DROP INDEX IF EXISTS idx_works_title_tri;
DROP INDEX IF EXISTS idx_works_abstract_tsv;
DROP INDEX IF EXISTS idx_works_abstract_tri;
DROP INDEX IF EXISTS idx_works_ta_tsv;

ALTER TABLE openalex.works
ALTER COLUMN ts_title SET to_tsvector('simple',title),
ALTER COLUMN ts_abstract SET to_tsvector('simple',abstract);

ALTER TABLE openalex.works
ALTER COLUMN ts_ta SET ts_title || ts_abstract;

COMMIT;

CREATE INDEX idx_works_title_tsv ON openalex.works USING gin (ts_title);
CREATE INDEX idx_works_title_tri ON openalex.works USING gin (title gin_trgm_ops);

CREATE INDEX idx_works_abstract_tsv ON openalex.works USING gin (ts_abstract);
CREATE INDEX idx_works_abstract_tri ON openalex.works USING gin (abstract gin_trgm_ops);

CREATE INDEX idx_works_ta_tsv ON openalex.works USING gin (ts_ta);