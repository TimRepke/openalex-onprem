# Merge snapshots
This command is used to check which abstracts from an old snapshot are missing in the current solr index and writes those to the index and the meta-cache database.

Example run
```bash
ssh 10.10.12.41
cd /mnt/bulk/openalex/nacsos-academic-search
uv run --no-sources openalex_ingest snapshot retain-old --snapshot ../james/OpenAlexArchive/JsonSnapshot --processed-partitions ../processed.txt --config conf/secret-prod.env --batch-size 5000

# This is a second run after already processing ~200M of which 20M records had an abstract
# 2026-04-02 17:38:19,142 [INFO] openalex-backup (2129071): Processed 130,500,000 so far of which 99,489,309 had an abstract of which 94,070,921 were found by ID in solr of which 19,264,350 did not have an abstract in solr
# 2026-04-02 17:43:01,567 [INFO] openalex-backup (2129071): Done after processing 130,654,267  of which 99,501,064 had an abstract of which 19,265,919 were not in solr
```
 