# Solr snapshot

## Steps to update snapshot
#### 1. Update S3 bucket
```
# connect to 
ssh srv-mcc-apsis  # 10.10.12.41 or srv-mcc-apsis-rechner
# open tmux session

cd /mnt/bulk/openalex

aws s3 sync "s3://openalex/data/jsonl/works" "openalex-snapshot/data/jsonl/works" --no-sign-request --delete
```

#### 2. Create an empty solr instance with all configurations
Make sure the binaries are up-to-date or the same as current production.

Relevant config in `/mnt/bulk/openalex/tmp_data/solr/bin/solr.in.sh`
```
SOLR_HEAP="2g"
SOLR_PID_DIR=/mnt/bulk/openalex/tmp_data/solr-home
SOLR_HOME=/mnt/bulk/openalex/tmp_data/solr-home
SOLR_DATA_HOME=/mnt/bulk/openalex/tmp_data/solr-home/data
SOLR_LOGS_DIR=/mnt/bulk/openalex/tmp_data/solr-home/logs
SOLR_PORT=8984
SOLR_MODULES=sql,clustering
SOLR_OPTS="$SOLR_OPTS -Denable.packages=true -Dsolr.modules=sql,clustering"
SOLR_OPTS="$SOLR_OPTS -Dsolr.max.booleanClauses=10000"
SOLR_OPTS="$SOLR_OPTS -DdistribUpdateConnTimeout=120000"
SOLR_OPTS="$SOLR_OPTS -DdistribUpdateSoTimeout=120000"
SOLR_OPTS="$SOLR_OPTS -DzkClientTimeout=120000"
SOLR_OPTS="$SOLR_OPTS -DsocketTimeout=120000"
SOLR_OPTS="$SOLR_OPTS -DconnTimeout=120000"
```

Start instance
```bash
% cd /mnt/bulk/openalex/tmp_data
% mkdir -p solr-home/data
% mkdir -p solr-home/logs
% solr/bin/solr start
```

Using `/mnt/bulk/openalex/nacsos-academic-search/conf/secret-temp.env`
```
NACSOS_OPENALEX__SNAPSHOT_DIR="/mnt/bulk/openalex/openalex-snapshot"

NACSOS_OPENALEX__SOLR_ENDPOINT="http://localhost:8984"
NACSOS_OPENALEX__SOLR_COLLECTION="openalex"
NACSOS_OPENALEX__SOLR_USER=
NACSOS_OPENALEX__SOLR_PASSWORD=

NACSOS_OPENALEX__SOLR_BIN="/mnt/bulk/openalex/tmp_data/solr/bin"
NACSOS_OPENALEX__SOLR_HOME="/mnt/bulk/openalex/tmp_data/solr-home"
NACSOS_OPENALEX__SOLR_HOST="127.0.0.1"
NACSOS_OPENALEX__SOLR_PORT=8984
NACSOS_OPENALEX__SOLR_ZOO_PORT=8984
```

Run `/mnt/bulk/openalex/nacsos-academic-search/src/openalex_ingest/snapshot/scripts/02_solr_setup.sh --config /mnt/bulk/openalex/nacsos-academic-search/conf/secret-temp.env`

#### 3. Ingest snapshot
```bash
cd /mnt/bulk/openalex/nacsos-academic-search
uv run snapshot snapshot ingest --snapshot=/mnt/bulk/openalex/openalex-snapshot --config-file=conf/secret-test.env \
 --post-batchsize=50000 --read-batchsize=100000 --commit-interval=100000 --collection=base
```

#### 4. Gap filling
We have a few "fixed" abstracts in a database for where they are missing in openalex.
We keep track of what was already transferred to the snapshot.
On rebuild, this also needs to be reset.
This takes a *long* time (an hour or so).
```sql
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
            WHERE solarized IS NOT NULL-- AND wrapper IN ('OpenAlex_old', 'NACSOS')
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
```

First, we want to make sure we are not loosing more, so we are processing our snapshot to check against the current solr
instance if we are not missing something.
```bash
rm /mnt/bulk/openalex/retained.txt
cd /mnt/bulk/openalex/nacsos-academic-search
uv run snapshot snapshot retain-old --snapshot=/mnt/bulk/openalex/openalex-snapshot --config=conf/secret-prod.env \
 --processed-partitions=/mnt/bulk/openalex/retained.txt --batch-size=10000
```

Now, we can fill the gaps in the temporary solr index.
```bash
cd /mnt/bulk/openalex/nacsos-academic-search
uv run snapshot fix transfer --config=conf/secret-test.env \
   --read-batch-size=10000 --post-batch-size=10000 --commit-interval=50000 \
   --no-force-overwrite
```

#### 6. Swap
```bash
sudo systemctl stop solr
cd /srv/solr
mv solr-home solr-home.bak
cp -r /mnt/bulk/openalex/openalex-snapshot/tmp_data/solr-home .
sudo systemctl start solr

# after verifying things are working properly, drop backup
rm -r solr-home.bak
```




Suggested/adapted
```
[Unit]
Description=Apache SOLR
After=network.target
StartLimitIntervalSec=10
StartLimitBurst=5

[Service]
#Type=forking
Type=simple
User=solr
WorkingDirectory=/srv/solr
Environment=SOLR_INCLUDE=/srv/solr/solr/bin/solr.in.sh
LimitNPROC=65000
LimitNOFILE=65000
PIDFile=/srv/solr/solr-home/solr-8983.pid
#ExecStart=/srv/solr/solr/bin/solr start -c -p 8983 --host 0.0.0.0 -m 25g -s /srv/solr/solr-home -Denable.packages=true -Dsolr.modules=sql,clustering -Dsolr.max.booleanClauses=10000
ExecStart=/srv/solr/solr/bin/solr start -p 8983 --host 0.0.0.0
ExecReload=/srv/solr/solr/bin/solr restart -p 8983
ExecStop=/srv/solr/solr/bin/solr stop -p 8983
#Restart=on-failure
Restart=always
RestartSec=3s
#TimeoutSec=180s
#PrivateTmp=true

[Install]
WantedBy=multi-user.target
```



## Maintenance

In case you need to add another field.
Don't forget to update the managed schema xml in case we need to run a full snapshot import at some point.
```bash
 curl -X POST -H 'Content-type:application/json' \
  http://10.10.12.41:8983/solr/openalex/schema \
  -d '{
    "add-field": {
      "name": "abstract_date",
      "type": "oa_date",  
    }
  }'
```

# Changing field type
You might want to change the tokeniser. Here's how:
```bash
# change schema
curl -X POST -H 'Content-type:application/json' --data-binary '{
  "replace-field-type": {
    "name": "oa_text",
    "class": "solr.TextField",
    "positionIncrementGap": "100",
    "docValues": false,
    "multiValued": false,
    "indexed": true,
    "stored": true,
    "indexAnalyzer": {
      "tokenizer": {
        "name": "standard",
        "maxTokenLength": 127
      },
      "filters": [
        { "name": "stop", "ignoreCase": true, "words": "stopwords.txt" },
        { "name": "lowercase" }
      ]
    },
    "queryAnalyzer": {
      "tokenizer": {
        "name": "standard",
        "maxTokenLength": 127
      },
      "filters": [
        { "name": "lowercase" }
      ]
    }
  }
}' http://10.10.12.41:8983/solr/openalex/schema

# sync
curl "http://10.10.12.41:8983/solr/admin/collections?action=RELOAD&name=openalex"

# reindex (effectively creates a new collection and copies things over and swaps it after it's done)
curl "http://10.10.12.41:8983/solr/admin/collections?action=REINDEXCOLLECTION&name=openalex&rows=100000&async=REPLACEME&cmd=start"

# check status
curl "http://10.10.12.41:8983/solr/admin/collections?action=REINDEXCOLLECTION&name=openalex&cmd=status"

# When you abort, you need to delete by ID (the &async param)
curl "http://10.10.12.41:8983/solr/admin/collections?action=REINDEXCOLLECTION&name=openalex&cmd=abort"
curl "http://10.10.12.41:8983/solr/admin/collections?action=REQUESTSTATUS&requestid=REPLACEME&cmd=delete"
```