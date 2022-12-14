CREATE EXTENSION pg_trgm;
CREATE EXTENSION btree_gin;

-- ## ABSTRACTS ## --

CREATE TEMP TABLE tmp_abstracts (
    data jsonb
    );

COPY tmp_abstracts(data)
FROM '/var/data/semanticscholar/json_outputs/abstracts.jsonl'
csv quote e'\x01' delimiter e'\x02';

WITH tmp as (
SELECT
(data ->> 'corpusid')::text as corpus_id,
(data #>> '{openaccessinfo,externalids,DOI}')::text as doi,
(data #>> '{openaccessinfo,externalids,MAG}')::text as mag_id,
(data ->> 'abstract')::text as abstract,
(data #>> '{openaccessinfo,status}')::text as open_access_status,
(data #>> '{openaccessinfo,license}')::text as open_access_license,
(data #>> '{openaccessinfo,url}')::text as open_access_url,
data #> '{openaccessinfo,externalids}' as external_ids,
(data ->> 'updated')::timestamp as updated_date
FROM tmp_abstracts
)

INSERT INTO s2.abstracts SELECT DISTINCT ON (corpus_id) * FROM tmp
ON CONFLICT (corpus_id) DO UPDATE SET
    doi = EXCLUDED.doi,
    mag_id = EXCLUDED.mag_id,
    abstract = EXCLUDED.abstract,
    open_access_status = EXCLUDED.open_access_status,
    open_access_license = EXCLUDED.open_access_license,
    open_access_url = EXCLUDED.open_access_url,
    external_ids = EXCLUDED.external_ids,
    updated_date = EXCLUDED.updated_date;

DROP TABLE tmp_abstracts;

-- ## AUTHORS ## --

CREATE TEMP TABLE tmp_authors (
    data jsonb
);

COPY tmp_authors(data)
FROM '/var/data/semanticscholar/json_outputs/authors.jsonl'
csv quote e'\x01' delimiter e'\x02';

with tmp as (
  SELECT
  (data ->> 'authorid')::text as author_id,
  data -> 'externalids' as external_ids,
  (data ->> 'name')::text as name,
  data -> 'aliases' as aliases,
  (data ->> 'url')::text as url,
  (data ->> 'homepage')::text as homepage,
  data -> 'affiliations' as affiliations,
  (data ->> 'papercount')::int as paper_count,
  (data ->> 'citationcount')::int as citation_count,
  (data ->> 'hindex')::int as hindex,
  (data ->> 'updated')::timestamp as updated_date
  FROM tmp_authors
)

INSERT INTO s2.authors SELECT DISTINCT ON (author_id) * FROM tmp
ON CONFLICT (author_id) DO UPDATE SET
    external_ids = EXCLUDED.external_ids,
    name = EXCLUDED.name,
    aliases = EXCLUDED.aliases,
    url = EXCLUDED.url,
    homepage = EXCLUDED.homepage,
    affiliations = EXCLUDED.affiliations,
    paper_count = EXCLUDED.paper_count,
    citation_count = EXCLUDED.citation_count,
    hindex = EXCLUDED.hindex,
    updated_date = EXCLUDED.updated_date;

DROP TABLE tmp_authors;

-- ## CITATIONS ## --

-- ## PAPERS ## --

CREATE TEMP TABLE tmp_papers (
    data jsonb
    );

COPY tmp_papers(data)
FROM '/var/data/semanticscholar/json_outputs/papers.jsonl'
csv quote e'\x01' delimiter e'\x02';

WITH tmp AS (SELECT
(data ->> 'corpusid')::text as corpus_id,
(data #>> '{externalids,DOI}')::text as doi,
(data #>> '{externalids,MAG}')::text as mag_id,
data -> 'externalids' as external_ids,
(data ->> 'title')::text as title,
(data ->> 'year')::int as publication_year,
(data -> 'venue')::text as publication_venue,
data -> 'authors' as authors,
(data ->> 'isopenaccess')::bool as is_open_access,
(data ->> 'url')::text as url,
data -> 's2fieldsofstudy' as s2_fields_of_study,
(data ->> 'citationcount')::int as citation_count,
(data ->> 'referencecount')::int as reference_count,
(data ->> 'influentialcitationcount')::int as influential_citation_count,
(data ->> 'updated')::timestamp as updated_date
FROM tmp_papers)

INSERT INTO s2.papers SELECT DISTINCT ON (corpus_id) * FROM tmp
ON CONFLICT (corpus_id) DO UPDATE SET
    doi = EXCLUDED.doi,
    mag_id = EXCLUDED.mag_id,
    external_ids = EXCLUDED.external_ids,
    title = EXCLUDED.title,
    publication_year = EXCLUDED.publication_year,
    publication_venue = EXCLUDED.publication_venue,
    authors = EXCLUDED.authors,
    is_open_access = EXCLUDED.is_open_access,
    url = EXCLUDED.url,
    s2_fields_of_study = EXCLUDED.s2_fields_of_study,
    citation_count = EXCLUDED.citation_count,
    reference_count = EXCLUDED.reference_count,
    influential_citation_count = EXCLUDED.influential_citation_count,
    updated_date = EXCLUDED.updated_date;

DROP TABLE tmp_papers;

-- ## S2ORC ## --

CREATE TEMP TABLE tmp_s2orc (
    data jsonb
    );

COPY tmp_s2orc(data)
FROM '/var/data/semanticscholar/json_outputs/s2orc.jsonl'
csv quote e'\x01' delimiter e'\x02';

with tmp as (SELECT
(data ->> 'corpusid')::text corpus_id,
(data #>> '{externalids,doi}')::text doi,
(data #>> '{externalids,mag}')::text mag_id,
(data -> 'externalids') external_ids,
(data #> '{content,source,oainfo}') open_access_metadata,
quote_nullable(data #>> '{content,text}')::text as full_text,
(data #> '{content,annotations}') annotations,
(data ->> 'updated')::timestamp updated_date
FROM tmp_s2orc)

INSERT INTO s2.s2orc SELECT DISTINCT ON (corpus_id) * FROM tmp
ON CONFLICT (corpus_id) DO UPDATE SET
    doi = EXCLUDED.doi,
    mag_id = EXCLUDED.mag_id,
    external_ids = EXCLUDED.external_ids,
    open_access_metadata = EXCLUDED.open_access_metadata,
    full_text = EXCLUDED.full_text,
    annotations = EXCLUDED.annotations,
    updated_date = EXCLUDED.updated_date;

DROP TABLE tmp_s2orc;

-- ## TLDRS ## --

CREATE TEMP TABLE tmp_tldrs (
    data jsonb
    );

COPY tmp_tldrs(data)
FROM '/var/data/semanticscholar/json_outputs/tldrs.jsonl'
csv quote e'\x01' delimiter e'\x02';

with tmp as (
SELECT
(data ->> 'corpusid')::text as corpus_id,
(data ->> 'model')::text as model,
(data ->> 'text')::text as summary
FROM tmp_tldrs
)

INSERT INTO s2.tldrs SELECT DISTINCT ON (corpus_id) * FROM tmp
ON CONFLICT (corpus_id) DO UPDATE SET
    model = EXCLUDED.model,
    summary = EXCLUDED.summary;

DROP TABLE tmp_tldrs;