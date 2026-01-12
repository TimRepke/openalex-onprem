# Evaluating impacts and mitigation strategies of missing abstracts

```bash
cd /mnt/bulk/openalex
# Process snapshot and extract all works IDs
python 01_extract_ids.py openalex-snapshot oa_ids.txt
# Select random sample of IDs
shuf -n 1000000 oa_ids.txt > oa_ids_sample.txt

```