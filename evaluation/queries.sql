-- Results not matched to OpenAlex
SELECT count(1)                                                                 as n_total,
       count(1) filter ( where openalex_id IS NULL )                            as n_missing_oa_id,
       count(1) filter ( where wrapper = 'DIMENSIONS' )                         as n_dimensions,
       count(1) filter ( where wrapper = 'SCOPUS' )                             as n_scopus,
       count(1) filter ( where wrapper = 'PUBMED' )                             as n_pubmed,
       count(1) filter ( where wrapper = 'WOS' )                                as n_wos,
       count(1) filter ( where wrapper = 'DIMENSIONS' AND openalex_id IS NULL ) as n_dimensions_no_oa,
       count(1) filter ( where wrapper = 'SCOPUS' AND openalex_id IS NULL )     as n_scopus_no_oa,
       count(1) filter ( where wrapper = 'PUBMED' AND openalex_id IS NULL )     as n_pubmed_no_oa,
       count(1) filter ( where wrapper = 'WOS' AND openalex_id IS NULL )        as n_wos_no_oa
FROM request
WHERE abstract IS NOT NULL
  AND time_created >= '2026-04-05';

-- Results with abstract
SELECT count(1)                                                                  as n_total,
       count(1) filter ( where openalex_id IS NULL )                             as n_missing_oa_id,
       count(1) filter ( where wrapper = 'DIMENSIONS' )                          as n_dimensions,
       count(1) filter ( where wrapper = 'SCOPUS' )                              as n_scopus,
       count(1) filter ( where wrapper = 'PUBMED' )                              as n_pubmed,
       count(1) filter ( where wrapper = 'WOS' )                                 as n_wos,
       count(1) filter ( where wrapper = 'DIMENSIONS' AND abstract IS NOT NULL ) as n_dimensions_abs,
       count(1) filter ( where wrapper = 'SCOPUS' AND abstract IS NOT NULL )     as n_scopus_abs,
       count(1) filter ( where wrapper = 'PUBMED' AND abstract IS NOT NULL )     as n_pubmed_abs,
       count(1) filter ( where wrapper = 'WOS' AND abstract IS NOT NULL )        as n_wos_abs,
       count(1) filter ( where wrapper = 'DIMENSIONS' AND openalex_id IS NULL AND abstract IS NOT NULL ) as n_dimensions_no_oa,
       count(1) filter ( where wrapper = 'SCOPUS' AND openalex_id IS NULL  AND abstract IS NOT NULL)     as n_scopus_no_oa,
       count(1) filter ( where wrapper = 'PUBMED' AND openalex_id IS NULL AND abstract IS NOT NULL )     as n_pubmed_no_oa,
       count(1) filter ( where wrapper = 'WOS' AND openalex_id IS NULL  AND abstract IS NOT NULL)        as n_wos_no_oa
FROM request
WHERE time_created >= '2026-04-05';

SELECT *
FROM request
WHERE wrapper = 'WOS'
  AND doi IS NULL;

-- Number of queued entries per remaining source count
SELECT jsonb_array_length(sources) as num_sources, count(1)
FROM queue
WHERE time_created > '2026-03-08'
GROUP BY num_sources;

SELECT
  record_id,
  openalex_id,
  doi,
  jsonb_path_query_first(
    raw,
    '$.dynamic_data.cluster_related.identifiers.identifier[*] ? (@.type == "xref_doi" || @.type == "doi").value'
  )#>>'{}' AS raw_doi
FROM request
WHERE wrapper='WOS'
LIMIT 100;

SELECT *from(SELECT
  record_id,
  openalex_id,
  doi,
  raw,
  abstract,
  jsonb_path_query_first(
    raw,
    '$.dynamic_data.cluster_related.identifiers.identifier[*] ? (@.type == "openalexworkID").value'
  )#>>'{}' AS raw_doi
FROM request
WHERE wrapper='WOS') where raw_doi is not null;-- and abstract is not null;
