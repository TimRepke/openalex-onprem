# Abstract backfilling for specific records

Collect OpenAlex IDs you want backfilling for.
For example, using random sample (check `evaluation/` or ask Max).

Then you queue the IDs from a file and let the queue worker rip like so

```bash
uv run src/openalex_ingest/scripts/queue_ids_for_backfill.py --source data/random_ids.txt --config conf/secret-local.env --loglevel DEBUG --batch-size 5000

uv run openalex_ingest queue-qorker ... 
```