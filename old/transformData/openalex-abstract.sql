ALTER TABLE openalex.works
ADD COLUMN abstract text;

WITH upd AS (
  SELECT id, array_to_string(ARRAY_AGG(b.key ORDER BY c.value::INT),' ') abstract
  FROM openalex.works a
  JOIN json_each(abstract_inverted_index) b ON TRUE
  JOIN json_array_elements_text(b.value) c ON TRUE
  GROUP BY 1 )

UPDATE openalex.works
SET abstract = upd.abstract
FROM upd
WHERE openalex.works.id = upd.id;

CREATE INDEX IF NOT EXISTS idx_works_abstract_tsv ON openalex.works USING gin (to_tsvector('english',abstract));
CREATE INDEX IF NOT EXISTS idx_works_abstract_tri ON openalex.works USING gin (abstract gin_trgm_ops);