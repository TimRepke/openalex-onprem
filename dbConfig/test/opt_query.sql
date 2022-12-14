-- Complex Where Statement (Query 1)

EXPLAIN ANALYZE
SELECT *
FROM openalex.abstracts a
LEFT JOIN openalex.works_filtered b
ON a.id = b.id
WHERE a.ts_abstract @@ (to_tsquery('english','(carbon | co2 | (carbon <-> dioxide)) <-> (capture <2> storage)')
 || to_tsquery('english','(co2 | (carbon <-> dioxide)) <3> ((capture | recovery) <2> sequestration)')
 || to_tsquery('english','((co2 | (carbon <-> dioxide)) <3> (captur* | stor* | recover* | extrac*)) & (post <-> combustion | scrub*)'));

-- Broader Criteria (Query 2)

EXPLAIN ANALYZE
SELECT c.display_name
	, c.publisher
    , c.homepage_url
	, COUNT(*) documents
    , COUNT(CASE WHEN a.type = 'journal-article' THEN a.id END) journal_documents
    , COUNT(CASE WHEN a.type != 'journal-article' THEN a.id END) other_documents
    , SUM(CASE WHEN a.type IS NULL THEN 1 ELSE 0 END) no_type_documents
FROM openalex.works_filtered a
LEFT JOIN openalex.works_host_venues b
ON a.id = b.work_id
LEFT JOIN openalex.venues c
ON b.venue_id = c.id
WHERE to_tsvector('english', a.title) @@ (to_tsquery('english','carbon'))
GROUP BY 1,2,3
ORDER BY 4 DESC;