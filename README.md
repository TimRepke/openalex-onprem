# Self-hosted academic search
The folder `old` contains work by Joe on the exploration of self-hosting OpenAlex, CORE, SemanticScholar, and other databases.

## Updating OpenAlex
The general "strategy" is as follows:

1. Sync S3 bucket
2. Pre-process (new) partitions for solr and postgres
3. Ingest pre-processed files into solr and postgres
4. Delete merged objects from solr and postgres

The `openalex-ingest` folder contains the necessary scripts to handle all that.
In particular, the `update.sh` is all you need to run, check `./update.sh -h` for help.
All scripts are assumed to be executed from that folder!

## Install / setup
```bash
cd openalex-ingest
python -m virtualenv venv
source venv/bin/activate
pip install -r ../requirements.txt
```

Copy the `default.env` file to `secrets.env` and adjust the values accordingly.

## Prerequisites
Solr is up and running, schema and collection exist:

```bash
bin/solr start -c  -Denable.packages=true -Dsolr.modules=sql,clustering
```

Postgres is properly set up and database/relations exist.

In case you want to run the python script directly, make sure the Cython bit is compiled: 

```bash
cd shared/cyth
python setup.py build_ext --inplace
```


