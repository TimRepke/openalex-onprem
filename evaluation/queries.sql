SELECT count(1) as n_total,
       count(1) filter ( where openalex_id IS NULL ) as n_missing_oa_id,
       count(1) filter ( where wrapper = 'DIMENSIONS' ) as n_dimensions,
       count(1) filter ( where wrapper = 'SCOPUS' ) as n_scopus,
       count(1) filter ( where wrapper = 'PUBMED' ) as n_pubmed,
       count(1) filter ( where wrapper = 'WOS' ) as n_wos,
       count(1) filter ( where wrapper = 'DIMENSIONS' AND openalex_id IS NULL ) as n_dimensions_no_oa,
       count(1) filter ( where wrapper = 'SCOPUS' AND openalex_id IS NULL ) as n_scopus_no_oa,
       count(1) filter ( where wrapper = 'PUBMED' AND openalex_id IS NULL ) as n_pubmed_no_oa,
       count(1) filter ( where wrapper = 'WOS' AND openalex_id IS NULL ) as n_wos_no_oa
FROM request
WHERE abstract IS NOT NULL
AND time_created >= '2026-04-05';


SELECT *
FROM request
WHERE wrapper = 'WOS' AND doi IS NULL;