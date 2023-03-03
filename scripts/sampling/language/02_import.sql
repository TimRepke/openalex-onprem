CREATE TABLE testtables.langs
(
    id   text not null,
    lang text
);

COPY testtables.langs (id, lang)
    FROM '/var/data/openalex/langs_f.csv'
    WITH (FORMAT CSV , HEADER FALSE , DELIMITER ' ');

UPDATE openalex.works_all w
SET lang = v.lang
FROM testtables.langs v
WHERE w.id = v.id;
