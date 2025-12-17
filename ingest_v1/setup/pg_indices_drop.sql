DROP INDEX IF EXISTS oa.openalex.authors_author_id_idx;

DROP INDEX IF EXISTS oa.openalex.institutions_institution_id_idx;

DROP INDEX IF EXISTS oa.openalex.institutions_associations_parent_institution_id_idx;
DROP INDEX IF EXISTS oa.openalex.institutions_associations_child_institution_id_idx;

DROP INDEX IF EXISTS oa.openalex.institutions_concepts_institution_id_idx;
DROP INDEX IF EXISTS oa.openalex.institutions_concepts_concept_id_idx;

DROP INDEX IF EXISTS oa.openalex.publishers_publisher_id_idx;

DROP INDEX IF EXISTS oa.openalex.funders_funder_id_idx;

DROP INDEX IF EXISTS oa.openalex.concepts_concept_id_idx;

DROP INDEX IF EXISTS oa.openalex.concepts_ancestors_parent_concept_id_idx;
DROP INDEX IF EXISTS oa.openalex.concepts_ancestors_child_concept_id_idx;

DROP INDEX IF EXISTS oa.openalex.concepts_related_concept_a_id_idx;
DROP INDEX IF EXISTS oa.openalex.concepts_related_concept_b_id_idx;

DROP INDEX IF EXISTS oa.openalex.sources_source_id_idx;

DROP INDEX IF EXISTS oa.openalex.works_work_id_idx;
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

DROP INDEX IF EXISTS oa.openalex.works_references_src_work_id_idx;
DROP INDEX IF EXISTS oa.openalex.works_references_trgt_work_id_idx;

DROP INDEX IF EXISTS oa.openalex.works_related_work_a_id_idx;
DROP INDEX IF EXISTS oa.openalex.works_related_work_b_id_idx;

DROP INDEX IF EXISTS topics_topic_id_idx;
DROP INDEX IF EXISTS works_topics_work_id_idx;
DROP INDEX IF EXISTS works_topics_topic_id_idx;
