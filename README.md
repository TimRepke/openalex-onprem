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
cd /srv/solr

# starting solr
sudo -u solr solr/bin/solr start -c -h 0.0.0.0 -m 6g -s /srv/solr/solr-home -Denable.packages=true -Dsolr.modules=sql,clustering -Dsolr.max.booleanClauses=4096

# stop and monitor solr
sudo -u solr solr/bin/solr stop
sudo -u solr solr/bin/solr status

# copying config files via zookeeper
sudo -u solr solr/bin/solr zk cp file:managed-schema.xml zk:/configs/._designer_openalex/managed-schema.xml -z 127.0.0.1:9983
```

Postgres is properly set up and database/relations exist.

```bash
# Create all relations in the "openalex" schema via:
psql setup/pg_schema.sql
# (optional) create users by editing the following file and then running
psql setup/pg_users.sql
```

In case you want to run the python script directly, make sure the Cython bit is compiled: 

```bash
cd shared/cyth
python setup.py build_ext --inplace
```


## Examples

Assuming you already synced to the latest OpenAlex snapshot and you only want to flatten files for the initial 
postgres import (not deleting flattened files after done and not generating deletion files);
```bash
./update.sh /home/rept/openalex/tmp_dir --skip-sync --skip-solr --skip-del --skip-clean --jobs 20
```

Only running initial solr import 

```bash
./update.sh /mnt/bulk/openalex/tmp_dir/ --skip-sync --skip-pg --skip-clean --skip-del
```