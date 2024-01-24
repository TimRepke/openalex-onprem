CREATE INDEX IF NOT EXISTS works_id_doi_idx ON openalex.works USING hash (id_doi);
CREATE INDEX IF NOT EXISTS works_publication_year_idx ON openalex.works USING btree (publication_year);

CREATE INDEX IF NOT EXISTS works_authorships_work_id_idx ON openalex.works_authorships USING hash (work_id);
CREATE INDEX IF NOT EXISTS works_authorships_author_id_idx ON openalex.works_authorships USING hash (author_id);

CREATE INDEX IF NOT EXISTS works_authorship_institutions_author_id_idx ON openalex.works_authorship_institutions USING hash (author_id);
CREATE INDEX IF NOT EXISTS works_authorship_institutions_work_id_idx ON openalex.works_authorship_institutions USING hash (work_id);
CREATE INDEX IF NOT EXISTS works_authorship_institutions_institution_id_idx ON openalex.works_authorship_institutions USING hash (institution_id);

CREATE INDEX IF NOT EXISTS works_locations_work_id_idx ON openalex.works_locations USING hash (work_id);
CREATE INDEX IF NOT EXISTS works_locations_source_id_idx ON openalex.works_locations USING hash (source_id);

CREATE INDEX IF NOT EXISTS works_concepts_work_id_idx ON openalex.works_concepts USING hash (work_id);
CREATE INDEX IF NOT EXISTS works_concepts_concept_id_idx ON openalex.works_concepts USING hash (concept_id);

CREATE INDEX IF NOT EXISTS works_sdgs_work_id_idx ON openalex.works_sdgs USING hash (work_id);
CREATE INDEX IF NOT EXISTS works_sdgs_sdg_id_idx ON openalex.works_sdgs USING hash (sdg_id);

CREATE INDEX IF NOT EXISTS works_related_work_a_id_idx ON openalex.works_related USING hash (work_a_id);
CREATE INDEX IF NOT EXISTS works_related_work_b_id_idx ON openalex.works_related USING hash (work_b_id);

CREATE INDEX IF NOT EXISTS works_references_work_a_id_idx ON openalex.works_references USING hash (work_a_id);
CREATE INDEX IF NOT EXISTS works_references_work_b_id_idx ON openalex.works_references USING hash (work_b_id);
