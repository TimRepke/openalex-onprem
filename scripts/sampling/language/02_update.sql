ALTER TABLE openalex.works_all ADD COLUMN IF NOT EXISTS lang varchar(3);

CREATE INDEX idx_works_all_lang ON openalex.works_all USING btree (lang);
