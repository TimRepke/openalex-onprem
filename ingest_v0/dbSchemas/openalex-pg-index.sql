
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Works

--CREATE INDEX idx_works_title ON openalex.works USING btree (title);
--CREATE INDEX idx_works_title_tsv ON openalex.works USING gin (to_tsvector('simple',title));
CREATE INDEX idx_works_title_tsv ON openalex.works USING gin (ts_title);
CREATE INDEX idx_works_title_tri ON openalex.works USING gin (title gin_trgm_ops);
CREATE INDEX idx_works_pubyear ON openalex.works USING btree (publication_year);
CREATE INDEX idx_works_type ON openalex.works USING btree (type);
CREATE INDEX idx_works_doi ON openalex.works USING btree (doi);

CREATE INDEX idx_works_abstract_tsv ON openalex.works USING gin (ts_abstract);
CREATE INDEX idx_works_abstract_tri ON openalex.works USING gin (abstract gin_trgm_ops);

CREATE INDEX idx_works_ta_tsv ON openalex.works USING gin (ts_ta);

-- Works Alternative Host Venues

CREATE INDEX idx_works_alt_host_ven_work_id ON openalex.works_alternate_host_venues USING btree (work_id);

-- Works Authorships

CREATE INDEX idx_works_authorships_work_id ON openalex.works_authorships USING btree (work_id);
CREATE INDEX idx_works_authorships_position ON openalex.works_authorships USING btree (author_position);
CREATE INDEX idx_works_authorships_author_id ON openalex.works_authorships USING btree (author_id);

-- Works Concepts

CREATE INDEX idx_works_concepts_work_id ON openalex.works_concepts USING btree (work_id);
CREATE INDEX idx_works_concepts_concept_id ON openalex.works_concepts USING btree (concept_id);

-- Works Host Venues

CREATE INDEX idx_works_host_venues_work_id ON openalex.works_host_venues USING btree (work_id);
CREATE INDEX idx_works_host_venues_venue_id ON openalex.works_host_venues USING btree (venue_id);

-- Works Referenced Works

CREATE INDEX idx_works_referenced_works_work_id ON openalex.works_referenced_works USING btree (work_id);
CREATE INDEX idx_works_referenced_Works_referenced_id ON openalex.works_referenced_works USING btree (referenced_work_id);

-- Authors

CREATE INDEX idx_authors_author_name ON openalex.authors USiNG btree (display_name);
CREATE INDEX idx_authors_author_name_tri ON openalex.authors USING gin (display_name gin_trgm_ops);
CREATE INDEX idx_authors_last_institution ON openalex.authors USING btree (last_known_institution);

-- Concepts

CREATE INDEX idx_concepts_display_name ON openalex.concepts USING btree (display_name);
CREATE INDEX idx_concepts_level ON openalex.concepts USING btree (level);

-- Concepts Ancestors

CREATE INDEX idx_concepts_ancestors_concept_id ON openalex.concepts_ancestors USING btree (concept_id);

-- Concepts Related Concepts

CREATE INDEX idx_concepts_related_concepts_concept_id ON openalex.concepts_related_concepts USING btree (concept_id);
CREATE INDEX idx_concepts_related_concepts_related_concept_id ON openalex.concepts_related_concepts USING btree (related_concept_id);

-- Institutions

CREATE INDEX idx_institutions_display_name ON openalex.institutions USING btree (display_name);
CREATE INDEX idx_institutions_country_code ON openalex.institutions USING btree (country_code);
CREATE INDEX idx_institutions_type ON openalex.institutions USING btree (type);

-- Venues

CREATE INDEX idx_venues_issn ON openalex.venues USING btree (issn_l);
CREATE INDEX idx_venues_display_name ON openalex.venues USING btree (display_name);
CREATE INDEX idx_venues_publisher ON openalex.venues USING btree (publisher);