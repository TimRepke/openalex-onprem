DROP INDEX IF EXISTS oa.openalex.works_id_doi_idx;
DROP INDEX IF EXISTS oa.openalex.works_publication_year_idx;

DROP INDEX IF EXISTS oa.openalex.works_authorships_work_id_idx;
DROP INDEX IF EXISTS oa.openalex.works_authorships_author_id_idx;

DROP INDEX IF EXISTS oa.openalex.works_authorship_institutions_author_id_idx;
DROP INDEX IF EXISTS oa.openalex.works_authorship_institutions_work_id_idx;
DROP INDEX IF EXISTS oa.openalex.works_authorship_institutions_institution_id_idx;

DROP INDEX IF EXISTS oa.openalex.works_locations_work_id_idx;
DROP INDEX IF EXISTS oa.openalex.works_locations_source_id_idx;

DROP INDEX IF EXISTS oa.openalex.works_concepts_work_id_idx;
DROP INDEX IF EXISTS oa.openalex.works_concepts_concept_id_idx;

DROP INDEX IF EXISTS oa.openalex.works_sdgs_work_id_idx;
DROP INDEX IF EXISTS oa.openalex.works_sdgs_sdg_id_idx;

DROP INDEX IF EXISTS oa.openalex.works_related_work_a_id_idx;
DROP INDEX IF EXISTS oa.openalex.works_related_work_b_id_idx;

DROP INDEX IF EXISTS oa.openalex.works_references_work_a_id_idx;
DROP INDEX IF EXISTS oa.openalex.works_references_work_b_id_idx;
