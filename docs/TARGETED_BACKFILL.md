# Abstract backfilling for specific records

You might want to back-fill abstracts for a targeted part of OpenAlex as best as possible.
Alternatively, you might want to do that for a random sample.

Then you queue the IDs from a file and let the queue worker run like so

```bash
# Draw random sample
uv run openalex_ingest  gapfilling sample-ids --target data/random_ids.txt --config conf/secret-local.env --target-size 1000000
# Queue IDs to meta-cache
uv run src/openalex_ingest/scripts/queue_ids_for_backfill.py --source data/random_ids.txt --config conf/secret-local.env --loglevel DEBUG --batch-size 5000

# Set up port forwarding for scopus
ssh -D 1080 foote -t bash
# Let queue worker rip
uv run openalex_ingest queue-worker --config=conf/secret-local.env --max-runtime=36000 --batch-size=25  --sources=DIMENSIONS --sources=SCOPUS --sources=PUBMED --sources=WOS --loglevel=DEBUG --min-abstract-len=25 --created-after=2026-04-08
```

Some queries to check how things are going
```sql
-- Check remaining queue
SELECT jsonb_array_length(sources) as num_sources, count(1)
FROM queue
WHERE time_created > '2026-03-08'
GROUP BY num_sources;

-- Get size of queue
SELECT count(1) from queue;

-- Get size of unfinished queue
SELECT count(1) from queue where jsonb_array_length(sources) > 0;

-- Drop accidentally added records from queue
DELETE FROM queue WHERE time_created>'2026-04-08';
```
