
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