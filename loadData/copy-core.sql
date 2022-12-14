CREATE SCHEMA IF NOT EXISTS core AUTHORIZATION joe;

CREATE TEMP TABLE tmp_core (
    data jsonb
    );

COPY tmp_core(data)
FROM PROGRAM 'cat /var/data/core/output/output/docs/*/*.jsonl'
csv quote e'\x01' delimiter e'\x02';

WITH tmp as (
SELECT
(data ->> 'coreId')::text as core_id,
(data ->> 'doi')::text as doi,
(data ->> 'magId')::text as mag_id,
(data ->> 'issn')::text as issn,
(data ->> 'oai')::text as oai,
data -> 'identifiers' as identifiers,
(data ->> 'title')::text as title,
(data ->> 'abstract')::text as abstract,
(data -> 'language') as work_language,
(data ->> 'fullTextIdentifier' is not null)::bool full_text_available,
data -> 'authors' as authors,
data -> 'contributors' as contributors,
(data ->> 'publisher')::text as publisher,
data -> 'journals' as publisher_journals,
(data ->> 'provider_id')::text as provider_id,
(data ->> 'year')::int as publication_year,
(data ->> 'datePublished')::text as publication_date,
data -> 'topics' as work_topics,
data -> 'subjects' as work_evaluation,
data -> 'enrichments' as work_enrichments,
data -> 'relations' as work_relations,
data -> 'urls' as work_urls,
(data ->> 'fullTextIdentifier')::text full_text_url
FROM tmp_core)

INSERT INTO core.works SELECT DISTINCT ON (core_id) * FROM tmp
ON CONFLICT (core_id) DO UPDATE SET
    doi = EXCLUDED.doi,
    mag_id = EXCLUDED.mag_id,
    issn = EXCLUDED.issn,
    oai = EXCLUDED.oai,
    identifiers = EXCLUDED.identifiers,
    title = EXCLUDED.title,
    abstract = EXCLUDED.abstract,
    work_language = EXCLUDED.work_language,
    full_text_available = EXCLUDED.full_text_available,
    authors = EXCLUDED.authors,
    contributors = EXCLUDED.contributors,
    publisher = EXCLUDED.publisher,
    publisher_journals = EXCLUDED.publisher_journals,
    provider_id = EXCLUDED.provider_id,
    publication_year = EXCLUDED.publication_year,
    publication_date = EXCLUDED.publication_date,
    work_topics = EXCLUDED.work_topics,
    work_evaluation = EXCLUDED.work_evaluation,
    work_enrichments = EXCLUDED.work_enrichments,
    work_relations = EXCLUDED.work_relations,
    work_urls = EXCLUDED.work_urls,
    full_text_url = EXCLUDED.full_text_url
    ;

DROP TABLE tmp_core;