# Solr snapshot

```bash

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