CREATE INDEX IF NOT EXISTS works_id_doi_idx ON openalex.works USING hash (id_doi);
CREATE INDEX IF NOT EXISTS works_publication_year_idx ON openalex.works USING btree (id_doi);

CREATE INDEX IF NOT EXISTS works_authorships_work_id_idx ON openalex.works_authorships USING hash (work_id);
CREATE INDEX IF NOT EXISTS works_authorships_author_id_idx ON openalex.works_authorships USING hash (author_id);

CREATE INDEX IF NOT EXISTS works_authorship_institutions_author_id_idx ON openalex.works_authorship_institutions USING hash (author_id);
CREATE INDEX IF NOT EXISTS works_authorship_institutions_work_id_idx ON openalex.works_authorship_institutions USING hash (work_id);
CREATE INDEX IF NOT EXISTS works_authorship_institutions_institution_id_idx ON openalex.works_authorship_institutions USING hash (institution_id);
