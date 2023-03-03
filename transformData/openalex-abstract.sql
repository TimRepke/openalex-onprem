CREATE TABLE IF NOT EXISTS openalex.abstracts
(
    id          text,
    doi         text,
    abstract    text,
    ts_abstract tsvector,
    PRIMARY KEY (id)
);

WITH upd AS (SELECT id,
                    doi,
                    array_to_string(ARRAY_AGG(b.key ORDER BY c.value::INT), ' ')                         abstract,
                    to_tsvector('english', array_to_string(ARRAY_AGG(b.key ORDER BY c.value::INT), ' ')) ts_abstract
             FROM openalex.works a
                      JOIN json_each(abstract_inverted_index) b ON TRUE
                      JOIN json_array_elements_text(b.value) c ON TRUE
             GROUP BY 1, 2)
INSERT
INTO openalex.abstracts
SELECT *
FROM upd
ON CONFLICT (id) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_oa_abstracts_tsv ON openalex.abstracts USING gin (ts_abstract);
CREATE INDEX IF NOT EXISTS idx_oa_abstracts_doi ON openalex.abstracts USING btree (doi);