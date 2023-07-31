-- This will empty all openalex tables in a matter of seconds. So be careful!
DELETE FROM oa.openalex.authors;
DELETE FROM oa.openalex.concepts;
DELETE FROM oa.openalex.concepts_ancestor;
DELETE FROM oa.openalex.concepts_related;
DELETE FROM oa.openalex.funders;
DELETE FROM oa.openalex.institutions;
DELETE FROM oa.openalex.institutions_association;
DELETE FROM oa.openalex.institutions_concept;
DELETE FROM oa.openalex.publishers;
DELETE FROM oa.openalex.sources;
DELETE FROM oa.openalex.works;
DELETE FROM oa.openalex.works_authorships;
DELETE FROM oa.openalex.works_concepts;
DELETE FROM oa.openalex.works_locations;
DELETE FROM oa.openalex.works_references;
DELETE FROM oa.openalex.works_related;