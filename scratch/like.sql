
EXPLAIN ANALYZE
SELECT *
FROM testtables.oa_works
WHERE to_tsvector('english', abstract) @@ to_tsquery('carbon <-> emissions');

EXPLAIN ANALYZE
SELECT *
FROM testtables.oa_works
WHERE abstract_tri LIKE '%carbon emissions%';