
```bash
$ solr/bin/solr start -Denable.packages=true -Dsolr.modules=sql,clustering
# OR
$ solr/bin/solr start -c -Denable.packages=true -Dsolr.modules=sql,clustering
# OR
$ bin/solr start -h 0.0.0.0 -V -p 8983 -m 5g -c -Denable.packages=true -Dsolr.modules=sql


$ carrot/carrot2/dcs/dcs
```

## CORS
add at opening of `web-app` in server/etc/webdefault.xml

```xml
    <filter>
        <filter-name>cross-origin</filter-name>
        <filter-class>org.eclipse.jetty.servlets.CrossOriginFilter</filter-class>
        <init-param>
            <param-name>allowedOrigins</param-name>
            <param-value>*</param-value>
        </init-param>
        <init-param>
            <param-name>allowedMethods</param-name>
            <param-value>GET,POST,OPTIONS,DELETE,PUT,HEAD</param-value>
        </init-param>
        <init-param>
            <param-name>allowedHeaders</param-name>
            <param-value>origin, content-type, accept</param-value>
        </init-param>
    </filter>

    <filter-mapping>
        <filter-name>cross-origin</filter-name>
        <url-pattern>/*</url-pattern>
    </filter-mapping>
```