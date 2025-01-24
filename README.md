# Self-hosted OpenAlex snapshot
* `openalex-ingest` hosts code to fetch, translate, and load the snapshot into solr and postgres
* `meta-cache` hosts a small service to cache external data for internal use that had to be removed from the public openalex snapshot


## OpenAlex meta-cache

### Proxies
Some publishers require you to contact them from a specific network.
This service assumes that you have set up proxies (e.g. SOCKS5 via `ssh -D 1080 [user]@[host] -t bash`) and that these proxies are correctly associated with api keys in the database.

### systemd

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