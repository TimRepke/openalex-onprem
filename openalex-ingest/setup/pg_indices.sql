CREATE INDEX IF NOT EXISTS authors_author_id_idx ON openalex.authors USING hash (author_id);

CREATE INDEX IF NOT EXISTS institutions_institution_id_idx ON openalex.institutions USING hash (institution_id);

CREATE INDEX IF NOT EXISTS institutions_associations_parent_institution_id_idx ON openalex.institutions_associations USING hash (parent_institution_id);
CREATE INDEX IF NOT EXISTS institutions_associations_child_institution_id_idx ON openalex.institutions_associations USING hash (child_institution_id);

CREATE INDEX IF NOT EXISTS institutions_concepts_institution_id_idx ON openalex.institutions_concepts USING hash (institution_id);
CREATE INDEX IF NOT EXISTS institutions_concepts_concept_id_idx ON openalex.institutions_concepts USING hash (concept_id);

CREATE INDEX IF NOT EXISTS publishers_publisher_id_idx ON openalex.publishers USING hash (publisher_id);

CREATE INDEX IF NOT EXISTS funders_funder_id_idx ON openalex.funders USING hash (funder_id);



CREATE INDEX IF NOT EXISTS works_doi_idx ON openalex.works USING hash (id_doi);
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

CREATE INDEX IF NOT EXISTS works_references_src_work_id_idx ON openalex.works_references USING hash (src_work_id);
CREATE INDEX IF NOT EXISTS works_references_trgt_work_id_idx ON openalex.works_references USING hash (trgt_work_id);
