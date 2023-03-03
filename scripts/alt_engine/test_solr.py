from pathlib import Path
import time
import csv
import json

with open('/home/tim/workspace/nacsos-academic-search/data/works_sample.csv') as csvfile:
    csvreader = csv.DictReader(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    docs = []
    for i, row in enumerate(csvreader):
        if i > 100:
            break
        docs.append(row)
    with open('/home/tim/workspace/nacsos-academic-search/data/works_sample.json', 'w') as fout:
        json.dump(docs, fout)

# SELECT title, abstract
# FROM openalex
# WHERE title = 'climate change'
# LIMIT 10;

# bin/solr start -p 8983 -c -Denable.packages=true