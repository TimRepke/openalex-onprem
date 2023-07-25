
```bash
cd openalex-solr
python setup.py build_ext --inplace
python msg.py
```


```bash
bin/solr start -c  -Denable.packages=true -Dsolr.modules=sql,clustering
```