
SELECT COUNT(1)
FROM openalex.works_filtered
WHERE to_tsvector('english', title) @@ to_tsquery('climate <-> change | carbon <-> emissions');

SELECT ts_headline('english', title, query)
FROM openalex.works_filtered,
     to_tsquery('english', 'climate <-> change | carbon <-> emissions') query
WHERE to_tsvector('english', title) @@ query
LIMIT 10;

SELECT count(1)
FROM openalex.works_filtered,
     to_tsquery('climate <-> change | carbon <-> emissions') query
WHERE query @@ to_tsvector('english', title);

SELECT count(1)
FROM openalex.works_filtered,
     to_tsquery('coal <-> commission') query
WHERE query @@ to_tsvector('english', title);

WITH relevant AS (SELECT title, query
                  FROM openalex.works_filtered,
                       to_tsquery('climate <-> change | carbon <-> emissions') query
                  WHERE query @@ to_tsvector('english', title))
SELECT title, ts_rank_cd(to_tsvector('english', title), query) AS rank
FROM relevant
ORDER BY rank DESC
LIMIT 10;

SELECT *
FROM openalex.works
WHERE to_tsvector('english', title) @@ websearch_to_tsquery('"climate change" or "carbon emissions"');

SELECT websearch_to_tsquery('"climate change" or "carbon emissions"');

SELECT *
FROM openalex.works a
         JOIN openalex.abstracts b
              ON a.id = b.id
WHERE to_tsvector('english', b.abstract) @@ websearch_to_tsquery('climate change')
OFFSET 4 LIMIT 5;

EXPLAIN ANALYZE
SELECT *
FROM openalex.works a
         JOIN openalex.abstracts b
              ON a.id = b.id
WHERE to_tsvector('english', a.title) || to_tsvector('english', b.abstract) @@ websearch_to_tsquery('climate change')
LIMIT 1;

SELECT *
FROM pg_indexes
WHERE schemaname = 's2'
ORDER BY tablename;

-- tmp
SELECT COUNT(*)
FROM openalex.works_filtered
WHERE to_tsvector('english', title) @@ websearch_to_tsquery('"climate change"');

-- bla
SELECT COUNT(1)
FROM openalex.works_filtered
WHERE to_tsvector('english', title) @@ websearch_to_tsquery('"climate change"');

SELECT ts_headline('english', 'gamify gamification', 'gamif:*'::tsquery);



SELECT 'real<3>world'::tsquery;
SELECT 'visiting'::tsquery;




-- ts_abstract vs ::tsquery
EXPLAIN ANALYSE
SELECT *
FROM openalex.abstracts b
WHERE b.ts_abstract @@ ('pric:* | (in-home<->display)')::tsquery
LIMIT 10000;

-- tsvector vs ::tsquery
EXPLAIN ANALYSE
SELECT *
FROM openalex.abstracts b
WHERE to_tsvector('english', b.abstract) @@ ('pric:* | in-home<->display')::tsquery
LIMIT 10000;

-- tsvector with join
EXPLAIN ANALYSE
SELECT *
FROM openalex.works_filtered a
         LEFT JOIN openalex.abstracts b ON a.id = b.id
WHERE (to_tsvector('english', a.title) || to_tsvector('english', b.abstract)) @@ ('pric:* | in-home<->display')::tsquery
LIMIT 1000;

-- ts_abstract with join
EXPLAIN ANALYSE
SELECT *
FROM openalex.works_filtered a
         LEFT JOIN openalex.abstracts b ON a.id = b.id
WHERE (to_tsvector('english', a.title) || b.ts_abstract) @@ ('pric:* | in-home<->display')::tsquery
LIMIT 1000;

-- ts_abstract with join and merged title+abstract
EXPLAIN ANALYSE
SELECT *
FROM openalex.works_filtered a
         LEFT JOIN openalex.abstracts b ON a.id = b.id
WHERE to_tsvector('english', a.title || b.abstract) @@ ('pric:* | in-home<->display')::tsquery
LIMIT 1000;


SELECT ts_headline('english', 'woman women', 'wom*n'::tsquery),
       ts_headline('english', 'woman women', to_tsquery('wom*n'));

SELECT *
FROM pg_stat_activity;


SELECT *
FROM (VALUES ('climate bli bla blu blo change'),
             ('climate bli bla blu change'),
             ('climate bli bla change'),
             ('climate bli change'),
             ('climate change'),
             ('change climate')) v(txt)
WHERE to_tsvector('simple', txt) @@ to_tsquery('simple', 'c:*');

EXPLAIN ANALYSE
SELECT count(1)
FROM (SELECT *
      FROM openalex.works_filtered
      WHERE to_tsvector('simple', title) @@
            ('(  household:* | residential | building | dormitor:* | individual ' ||
             '   | consumer:* | participant:* | customer:* | domestic | homeowner:* ' ||
             '  )') ::tsquery) a,
     (SELECT *
      FROM openalex.abstracts
      WHERE to_tsvector('simple', abstract) @@
            ('(  household:* | residential | building | dormitor:* | individual ' ||
             '   | consumer:* | participant:* | customer:* | domestic | homeowner:* ' ||
             '  )') ::tsquery) b
WHERE a.id = b.id
  AND (to_tsvector('simple', a.title) || to_tsvector('simple', b.abstract)) @@
      ('(  household:* | residential | building | dormitor:* | individual ' ||
       '   | consumer:* | participant:* | customer:* | domestic | homeowner:* ' ||
       '  )') ::tsquery;

SELECT *
FROM openalex.works_filtered
LIMIT 5;

SELECT *
FROM ts_debug('english', 'M.I.N.T.');

SELECT count(usename) OVER (PARTITION BY usename ) AS concurrent_statements, *
FROM pg_stat_activity;

SELECT pg_terminate_backend(pg_stat_activity.procpid)
 FROM pg_stat_get_activity(NULL::integer)
 WHERE datid=(SELECT oid from pg_database where user = 'tim');

SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.usename = 'tim' AND pg_stat_activity.datname = 'dev';