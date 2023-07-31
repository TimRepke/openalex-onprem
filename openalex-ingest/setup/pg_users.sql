-- User for updating the database
CREATE USER openalex_rw WITH LOGIN PASSWORD '<PASSWORD>';
GRANT CONNECT ON DATABASE oa TO openalex_rw;
GRANT ALL PRIVILEGES ON SCHEMA openalex TO openalex_rw;
GRANT pg_execute_server_program TO openalex_rw;
ALTER USER openalex_rw SUPERUSER ; -- FIXME a little over the top


-- User for reading the database
CREATE USER openalex WITH PASSWORD '<PASSWORD>';
GRANT CONNECT ON DATABASE oa TO openalex;
GRANT SELECT ON ALL TABLES IN SCHEMA openalex TO openalex;
