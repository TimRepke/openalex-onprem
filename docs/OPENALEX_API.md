Read data from OpenAlex API and write to solr

```bash
# Get stats about latest update
curl 'http://10.10.12.41:8983/solr/openalex/select?_=1769714129541&fl=created_date&indent=true&q=*:*&q.op=AND&stats=true&stats.field=created_date&useParams=' \
  -H 'Referer: http://10.10.12.41:8983/solr/' | jq '.stats'
curl 'http://10.10.12.41:8983/solr/openalex/select?_=1769714129541&fl=updated_date&indent=true&q=*:*&q.op=AND&stats=true&stats.field=updated_date&useParams=' \
  -H 'Referer: http://10.10.12.41:8983/solr/' | jq '.stats'

cd /var/www/nacsos-academic
uv sync --extra server
cd openalex-ingest
PYTHONPATH=. python daily/pull_api_update.py bulk --config=../conf/secret-prod.env --from-date 2025-11-11 --to-date 2026-01-29

# if needed, forward postgres port from VM to current machine
ssh -N -L 5000:localhost:5432 se164
```


bulk')
def bulk_api_pull(
    config: Annotated[Path, typer.Option(help='Path to config file')],
    from_date: Annotated[datetime, typer.Option(help='First day to start pulling updates from')],
    to_date: Annotated[datetime, typer.Option(help='Last day to include updates from')],
    solr_buffer_size: int = 200,
    loglevel: str = 'INFO',