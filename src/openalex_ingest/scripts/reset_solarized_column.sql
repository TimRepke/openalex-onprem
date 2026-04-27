-- If the solr index is reset, the meta-cache request table needs to be reset
-- Just running `UPDATE request SET solarized = null` takes forever. The following
-- is less resource intense and should take 1min/million records.
DO $$
DECLARE
    rows_updated INT;
BEGIN
    LOOP
        -- Update a chunk of 10,000 rows
        UPDATE request
        SET solarized = NULL
        WHERE record_id IN (
            SELECT record_id FROM request
            WHERE solarized IS NOT NULL
            LIMIT 10000
        );

        GET DIAGNOSTICS rows_updated = ROW_COUNT;

        -- Exit if there's nothing left to do
        EXIT WHEN rows_updated = 0;

        -- Commit the current batch so logs can clear
        COMMIT;
    END LOOP;
END $$;

-- Check statistics
SELECT wrapper, solarized, count(1)
from request
group by wrapper, solarized;