
CREATE TABLE testtables.oa_works (LIKE openalex.works_filtered INCLUDING INDEXES);

INSERT INTO testtables.oa_works
SELECT * FROM openalex.works_filtered
TABLESAMPLE SYSTEM (1);