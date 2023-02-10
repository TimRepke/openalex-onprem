ALTER TABLE openalex.works_all ADD COLUMN IF NOT EXISTS language varchar(3);

CREATE INDEX idx_works_all_language ON openalex.works_all USING btree (language);

UPDATE openalex.works_all SET lang = 'en' WHERE id = 'https://openalex.org/W2898085742';


