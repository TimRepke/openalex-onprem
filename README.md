# Self-hosted academic search

This repository hosts a series of helper scripts and some guidance on how to self-host [OpenAlex](https://docs.openalex.org/) in Solr and/or PostgreSQL.

These scripts can be used for the initial import and continuous updates of an existing database as snapshots are updated.

If you have any recommendations for improving the performance or better data structures, please get in touch by submitting a pull request or opening an issue.

The folder `old` contains work by Joe on the exploration of self-hosting OpenAlex, CORE, SemanticScholar, and other databases.

## Updating OpenAlex
The general "strategy" is as follows:

1. Sync S3 bucket
2. Pre-process (new) partitions for solr and postgres
3. Ingest pre-processed files into solr and postgres
4. Delete merged objects from solr and postgres

This repository root folder contains the necessary scripts to handle all that.
In particular, the `update.sh` is all you need to run, check `./update.sh -h` for help.
All scripts are assumed to be executed from that folder!

## Install / setup
```bash
python -m virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy the `default.env` file to `secrets.env` and adjust the values accordingly. See `shared/config.py` for some explanations.

## Prerequisites
Solr is up and running, schema and collection exist. See the setup folder for the schema and our `solr.in.sh`.
Here are some helpful commands for starting, stopping, or managing solr:

```bash
cd /srv/solr

# starting solr
sudo -u solr solr/bin/solr start -c -h 0.0.0.0 -m 20g -s /srv/solr/solr-home -Denable.packages=true -Dsolr.modules=sql,clustering -Dsolr.max.booleanClauses=4096

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
Note: The `tmp_dir` must have `rwx` permissions for the postgres user in order for this to work; files at least `r`.
You could get away with more restrictive permissions, but then you'd have to use `\copy` instead of `COPY`, which [the documentation says is slower](https://www.postgresql.org/docs/current/app-psql.html#APP-PSQL-META-COMMANDS-COPY).

All steps are skipped by default. The following assumes you have the latest version of the snapshot synced and runs the full solr/postgres import:
```bash
./update.sh /path/to/openalex/tmp_dir  --config secret.env --solr --solr-del --solr-clr --pg-del-ind --pg-del-dat --pg-del-upd --pg-flat --pg --pg-ind --pg-clr --jobs 15 --override
```

## Caveats
* Some objects in the current snapshot (as of 2023-08-01) do not adhere to the documentation. In these cases we do not always try to recover the data fully but do a low-hanging-fruit-best-effort.
* Some publishers do not have an ID, which violates the database constraint (private key). We do not import those, because we couldn't refer to them anyway.
* Some dehydrated objects in the work object are missing an ID. We still import them but leave the field empty in the many-to-many relations `works_authorships` and `works_locations`. This is not ideal and not pretty, but, for our use case, that seemed reasonable.
* In Solr, we have a `title_abstract` field that is essentially duplicated data of concatenated title and abstract. Although this takes more space, we *need* searches across title and abstract and this is the easiest solution.
* Solr does only contain fields from the works objects (and not even all of them). We think that if you need more details, you can use postgres.
* Solr includes nested objects and non-indexed json strings. This makes hosting much easier, but you can't properly filter for authors.

## Runtimes and storage
* The flattening of the whole snapshot for postgres takes around 1.5h, importing those flattened files takes around 15h. Note, that the latter can probably be improved significantly by tuning hosting parameters. If you do, please let us know.
* The Solr import (pre-processing and import happens simultaneously) takes around 12h.
* RAM usage of the scripts is below 200MB, since everything is processed sequentially and no big objects are kept in memory.
* The solr-home folder has a size of around 340GB after the initial full snapshot import.
* The openalex-snapshot folder has a size of around 312GB
* The flattened postgres files have a size of around 163GB
* The `/var/lib/postgresql/16/main/base` folder is around 1TB after the initial full snapshot import.
* The temporary solr files usually around 1GB, but since each partition is processed one-by-one, there's no significant storage need here.

## Some admin tricks
```bash
# See which postgres DBs are running
pg_lsclusters

# Create another database instance
pg_createcluster 16 main -p 5439  # change "main" and "5439"

# Adjust settings in the /etc/postgresql/[version]/[name]/hba_conf.conf
# (esp. connection via external IP and login as user)
# Adjust settings in the /etc/postgresql/[version]/[name]/postgres.conf
# (esp. listen_address=0.0.0.0 and port)

# Create the "oa" database
sudo -u postgres createdb -p 5433 oa
# Open SQL console
sudo -u postgres psql -p  5433 oa
```

## Some random solr things
```bash
sudo -u solr vim solr/bin/solr.in.sh
sudo -u solr vim solr/server/solr/solr.xml
sudo -u solr vim managed-schema.xml
sudo -u solr solr/bin/solr zk cp file:managed-schema.xml zk:/configs/._designer_openalex/managed-schema.xml -z 127.0.0.1:9983
sudo -u solr solr/bin/solr status
sudo -u solr solr/bin/solr stop -h 0.0.0.0
sudo -u solr solr/bin/solr start -c  -h 0.0.0.0 -m 20g -s /srv/solr/solr-home -Denable.packages=true -Dsolr.modules=sql,clustering -Dsolr.max.booleanClauses=4096
sudo -u solr solr/bin/solr start -c openalex -Denable.packages=true -Dsolr.modules=sql,clustering -Dhost=0.0.0.0 -memory=6g -solr.home=/srv/solr/solr-home -Dsolr.max.booleanClauses=4096 -Dsolr.jetty.host=0.0.0.0
sudo -u solr solr/bin/solr start -c -Denable.packages=true -Dsolr.modules=sql,clustering -Dhost=0.0.0.0 -memory=6g -d /srv/solr/solr-home -Dsolr.max.booleanClauses=4096 -Dsolr.jetty.host=0.0.0.0
sudo -u solr solr/bin/solr start -c -Denable.packages=true -Dsolr.modules=sql,clustering -h 0.0.0.0 -m 6g -d /srv/solr/solr-home -Dsolr.max.booleanClauses=4096 -h 0.0.0.0
```

## Solr as service
```
$ cat /etc/systemd/system/solr.service
[Unit]
Description=Apache SOLR
After=network.target

[Service]
Type=simple
User=solr
WorkingDirectory=/srv/solr
LimitNPROC=65000
LimitNOFILE=65000
PIDFile=/srv/solr/solr-home/pid/solr-8983.pid
ExecStart=/srv/solr/solr/bin/solr start -c -p 8983 -h 0.0.0.0 -m 20g -s /srv/solr/solr-home -Denable.packages=true -Dsolr.modules=sql,clustering -Dsolr.max.booleanClauses=4096
ExecReload=/srv/solr/solr/bin/solr restart -p 8983
ExecStop=/srv/solr/solr/bin/solr stop -p 8983
Restart=always

[Install]
WantedBy=multi-user.target
```

## sudoers
```
$ cat /etc/sudoers.d/gitlab
gitlab-runner ALL= NOPASSWD: /usr/bin/chgrp -R openalex /mnt/bulk/openalex/openalex-snapshot
gitlab-runner ALL= NOPASSWD: /usr/bin/chmod -R 775 /mnt/bulk/openalex/openalex-snapshot
gitlab-runner ALL= NOPASSWD: /usr/bin/chown -R solr\:solr /srv/solr/solr-home
gitlab-runner ALL= NOPASSWD: /usr/bin/chown -R gitlab-runner\:gitlab-runner /srv/solr/solr-home
gitlab-runner ALL= NOPASSWD: /usr/bin/chown -R gitlab-runner\:gitlab-runner /mnt/bulk/openalex/tmp_data/solr-home

gitlab-runner ALL= NOPASSWD: /usr/bin/systemctl start solr.service
gitlab-runner ALL= NOPASSWD: /usr/bin/systemctl stop solr.service
gitlab-runner ALL= NOPASSWD: /usr/bin/pg_createcluster 16 oastaging -p 5434 -d /mnt/bulk/openalex/tmp_data/pg -u postgres --start
gitlab-runner ALL=(postgres) NOPASSWD: /usr/bin/createdb -p 5434 oa
gitlab-runner ALL=(postgres) NOPASSWD: /usr/bin/psql -f /mnt/bulk/openalex/nacsos-academic-search/openalex-ingest/setup/pg_schema.sql -p 5434 -d oa --echo-all
gitlab-runner ALL=(postgres) NOPASSWD: /usr/bin/psql -f /mnt/bulk/openalex/nacsos-academic-search/openalex-ingest/setup/pg_users_secret.sql -p "5434 -d oa
```