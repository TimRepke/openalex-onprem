# Self-hosted OpenAlex snapshot

Check the `docs/` directory for more documentation!

```bash
uv sync 
# to install nacsos-data from remote
#uv sync --no-sources
```

## solr / ingest

Show min/max created_date and updated_date (params: stats=true, stats.field=updated_date)
 * http://10.10.12.41:8983/solr/#/openalex/query?q=*:*&q.op=AND&indent=true&fl=created_date&stats.field=created_date&stats=true&useParams=
 * http://10.10.12.41:8983/solr/#/openalex/query?q=*:*&q.op=AND&indent=true&fl=created_date&stats.field=updated_date&stats=true&useParams=

## OpenAlex meta-cache

### Proxies
Some publishers require you to contact them from a specific network.
This service assumes that you have set up proxies (e.g. SOCKS5 via `ssh -D 1080 [user]@[host] -t bash`) and that these proxies are correctly associated with api keys in the database.

### systemd

#### Permanent SSH tunnel
sudo cat /etc/systemd/system/pik-ssh.service
```
[Unit]
Description=Persistent SSH Tunnel to PIK on port 1080.
After=network.target

[Service]
Restart=on-failure
RestartSec=5
ExecStart=/usr/bin/ssh -D 1080 ??@ts01.pik-potsdam.de -NTC -o ServerAliveInterval=60 -o ExitOnForwardFailure=yes
User=??
Group=??

[Install]
WantedBy=multi-user.target
```

#### REST service
sudo cat /etc/systemd/system/openalex-cache.service
```
[Unit]
Description=OpenAlex Cache
After=network.target

[Service]
Type=simple
User=openalex
Group=openalex
Environment="OACACHE_CONFIG=/var/www/openalex-cache/nacsos-academic-search/meta_cache/config/server.env"
Environment="PYTHONPATH=$PYTHONPATH:/var/www/openalex-cache/nacsos-academic-search:/var/www/openalex-cache/nacsos-academic-search/meta_cache"
Environment="PYTHONUNBUFFERED=1"
WorkingDirectory=/var/www/openalex-cache/nacsos-academic-search/meta_cache
LimitNOFILE=4096
ExecStart=/var/www/openalex-cache/venv/bin/python -u -m hypercorn server.main:app --reload --config=config/hypercorn-server.toml
Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

#### Queue service
sudo cat /etc/systemd/system/openalex-cache-queue.service
```
Description=OpenAlex Cache Queue
After=network.target

[Service]
Type=simple
User=openalex
Group=openalex
Environment="OACACHE_CONFIG=/var/www/openalex-cache/nacsos-academic-search/meta_cache/config/server.env"
Environment="PYTHONPATH=$PYTHONPATH:/var/www/openalex-cache/nacsos-academic-search:/var/www/openalex-cache/nacsos-academic-search/meta_cache"
Environment="PYTHONUNBUFFERED=1"
WorkingDirectory=/var/www/openalex-cache/nacsos-academic-search/meta_cache
LimitNOFILE=4096
ExecStart=/var/www/openalex-cache/venv/bin/rq worker meta-cache-scopus meta-cache-dimensions meta-cache-openalex meta-cache-wos meta-cache-s2 meta-cache-pubmed
Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

#### sudoers
sudo cat /etc/sudoers.d/gitlab
```
# Allow GitLab Runner to transfer file ownership
gitlab-runner ALL= NOPASSWD: /usr/bin/chown -R gitlab-runner\:gitlab-runner /var/www/openalex-cache
gitlab-runner ALL= NOPASSWD: /usr/bin/chown -R openalex\:openalex /var/www/openalex-cache

# Allow GitLab Runner to start/stop services
gitlab-runner ALL= NOPASSWD: /usr/bin/systemctl restart openalex-cache-queue.service
gitlab-runner ALL= NOPASSWD: /usr/bin/systemctl stop openalex-cache-queue.service
gitlab-runner ALL= NOPASSWD: /usr/bin/systemctl start openalex-cache-queue.service
gitlab-runner ALL= NOPASSWD: /usr/bin/systemctl status openalex-cache-queue.service

gitlab-runner ALL= NOPASSWD: /usr/bin/systemctl restart openalex-cache.service
gitlab-runner ALL= NOPASSWD: /usr/bin/systemctl stop openalex-cache.service
gitlab-runner ALL= NOPASSWD: /usr/bin/systemctl start openalex-cache.service
gitlab-runner ALL= NOPASSWD: /usr/bin/systemctl status openalex-cache.service
```

## Notes
Checking of works with missing abstract:   
* on 2025-01-24 this gives 116,289,712 http://localhost:8983/solr/#/openalex/query?q=-abstract:%5B%22%22%20TO%20*%5D&q.op=AND&defType=lucene&indent=true&useParams=    
* on 2025-01-24 this gives 116,225,229 http://localhost:8983/solr/#/openalex/query?q=-abstract:*&q.op=AND&defType=lucene&indent=true&useParams=


## Linking OpenAlex Sources to Citation Indexes
We are interested in linking citation indexes to OpenAlex sources, so that they can be queried based on citation index if necessary. Linking is done through matching ISSNs or eISSNs.

- OpenAlex: https://developers.openalex.org/api-reference/sources/list-sources
    - Run `src/openalex_ingest/scripts/collect_openalex_sources.py` to collect sources and save them under `data`.
- Web of Science: https://www.webofscience.com/wos/mjl/collection-list-downloads loging with PIK email address to be able to download
    - Manually downloaded files are saved under `data/citation_indexes/webofsci`
- Scopus: Download from https://www.elsevier.com/products/scopus/content, under Titles on Scopus [here](https://downloads.ctfassets.net/o78em1y1w4i4/7xtaTxNiNcWRTeZkV86eNy/54b2e159af75b0de69128973f3030e3b/ext_list_May_2026).xlsx 
    - Saved under `data/citation_indexes/scopus`

Current list of index files are as below. The generated IDs for citation indexes are saved in `INDEX_NAMES_MAP`.json and a map of OpenAlex Source ID -> list of citation indexes it is included in are kept at `SOURCE_ID_TO_CITATION_INDEX_MAP.json`

```
data/citation_indexes
├── INDEX_NAMES_MAP.json
├── scopus
│   └── ext_list_May_2026.xlsx
├── SOURCE_ID_TO_CITATION_INDEX_MAP.json
└── webofsci
    ├── Arts & Humanities Citation Index (AHCI).csv
    ├── Biological Abstracts.csv
    ├── BIOSIS Previews_BIOSIS Citation Index.csv
    ├── BIOSIS Reviews Reports And Meetings.csv
    ├── Chemical Reactions.csv
    ├── Current Contents Agriculture, Biology & Environmental Sciences.csv
    ├── Current Contents Arts & Humanities.csv
    ├── Current Contents Business Collection.csv
    ├── Current Contents Clinical Medicine.csv
    ├── Current Contents Electronics & Telecommunications Collection.csv
    ├── Current Contents Engineering, Computing & Technology.csv
    ├── Current Contents Life Sciences.csv
    ├── Current Contents Physical, Chemical & Earth Sciences.csv
    ├── Current Contents Social And Behavioral Sciences.csv
    ├── Emerging Sources Citation Index (ESCI).csv
    ├── Essential Science Indicators.csv
    ├── Index Chemicus.csv
    ├── Science Citation Index Expanded (SCIE).csv
    ├── Social Sciences Citation Index (SSCI).csv
    └── Zoological Record.csv
```
Because the above files are raw data files, some data cleaning is necessary to remove duplicates and keep IDs in a format that is matchable to OpenAlex. The expected schemas for the data files are saved under schemas in pandera compatible yml files.
After processing SCOPUS_EXTLIST_2026-05 and latest citation indexes from June 2026 from Web of Science, source_id_to_index_ids has 103038 total matches (including multiple matches for a single source).