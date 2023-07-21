SELECT count(1) FILTER ( WHERE abstract is not null ) as filled,
       count(1) FILTER ( WHERE abstract is null )     as empty
FROM testtables.oa_works;

SELECT count(1) FILTER ( WHERE abstracts.ts_abstract is not null ) as filled,
       count(1) FILTER ( WHERE abstracts.ts_abstract is null )     as empty
FROM openalex.abstracts;

WITH years as (SELECT generate_series(1900, 2022, 1) as year)
SELECT y.year, count(1)
FROM years y
         LEFT JOIN openalex.works_all w ON y.year = w.publication_year
GROUP BY y.year
ORDER BY y.year;

SELECT count(1) -- -> 187,077,127 (88.6% of all)
FROM openalex.works_filtered;

SELECT count(1) -- -> 211,003,388
FROM openalex.works_all;
-- @61% en -> est.  128,710,000 records
--       10% sample: 12,871,000 records
--        5% sample:  6,435,500 records
--        1% sample:  1,287,100 records
--      0.5% sample:    643,550 records

WITH years as (SELECT generate_series(1900, 2022, 1) as year)
SELECT y.year, count(1)
FROM years y
         LEFT JOIN openalex.works_all w ON y.year = w.publication_year
WHERE to_tsvector('english', title) @@ to_tsquery('english', 'climate')
GROUP BY y.year
ORDER BY y.year;


WITH years as (SELECT generate_series(1900, 2022, 1) as year)
SELECT y.year, count(1)
FROM years y
         LEFT JOIN openalex.works_filtered w ON y.year = w.publication_year
WHERE to_tsvector('english', title) @@ to_tsquery('english', 'climate')
GROUP BY y.year
ORDER BY y.year;

SELECT count(1)
FROM openalex.works_all
WHERE lang is not null;

EXPLAIN (ANALYSE , BUFFERS )
WITH years as (SELECT generate_series(1990, 2023, 1) as year)
SELECT y.year,
       count(1)                                                        as cnt_all,
       count(1) FILTER ( WHERE w.lang = 'en' )                         as cnt_en,
       count(1) FILTER ( WHERE w.lang <> 'en' AND w.lang is not null ) as cnt_other,
       count(1) FILTER ( WHERE w.lang is null )                        as cnt_null
FROM years y
         LEFT JOIN openalex.works_all w ON y.year = w.publication_year
GROUP BY y.year
ORDER BY y.year;


SELECT lang, count(1) as num_works
FROM openalex.works_all
GROUP BY lang
ORDER BY num_works DESC;


EXPLAIN (ANALYSE , BUFFERS )
SELECT count(1)
FROM openalex.works_all
WHERE publication_year = 2000
  AND lang = 'en';

VACUUM VERBOSE ANALYSE openalex.works_all;

