# NACSOS Academic Search

Relevant ETL scripts for MCC's Open Academic postgresDB. 
Files are organized by their usage and named for their relevant schema.
Eventually these will all be streamlined into one set of scripts to run.

# Directories

---

## dbConfig

Contains dev and prod `postgresql.conf` files for postgresDB.

## dbSchemas

Contains `.sql` scripts for initializing schemas and indexes.

## downloadData
*This is a WIP*

Contains `.py` scripts to download datasets. 

## Instructions

Instructions saved as `.txt.` for loading schemas in DB. 
These are redundant instructions from the `Instructions for Loading Data by Database` header below.

## loadData

Contains `.sql` files for populating db schemas with relevant data.

## Main
*This is a WIP*

Contains main scripts to run all steps sequentially to create and populate schemas in db.

## transformData

Contains custom scripts to modify individual datasets to make the data more usable in the db.

# Individual DB Instructions

---

In the situation that the `Main` scripts become unusable or encounter errors,
use the following ETL instructions for each database.

## OpenAlex

To download the data or for more detailed ETL instructions for the postgres DB, 
please see [OpenAlex's documentation](https://docs.openalex.org/download-snapshot).
**NOTE**: The instructions below deviate significantly from the official documentation.

### Step 1: Convert JSONL Files to CSV

Run `flatten-openalex-jsonl.py`. This script assumes that you are reading from `openalex-snapshot/` in your
current directory and want to write into `csv-files/`. This can be changed in the script but will also require downstream changes.

**HINT**: By duplicating the script you can run file conversions in parallel which could reduce the time to complete. This
can be done by commenting out the functions in the `__main__()` function at the bottom of the script. Then simply
run the scripts simultaneously.

Example code snippet:

```bash
nohup python transformData/flatten-openalex-jsonl.py &
````

### Step 2: Initialize Schema

Run `dbSchemas/openalex-pg-schema.sql`. Replace the `{dbName}` variable with the database
you'd like to create the schema and tables within.

Example code snippet:

```bash
nohup psql -d {dbName} -f dbSchemas/openalex-pg-schema.sql &
````

### Step 3: Populate Tables

Run `loadData/copy-openalex-csv.sql` to copy csv-file subfolders into appropriate tables.
This script assumes it is run within the parent folder of `csv-files/`. If you changed the location
output in step 1, you will have to change the location in each instance of the copy script.

Example code snippet:

```bash
nohup psql -d {dbName} -f loadData/copy-openalex-csv.sql &
```

### Step 4: Initialize Indexes

Run `dbSchemas/openalex-pg-index.sql` to generate indexes. 
It's generally advisable to load all indexes after populating data to prevent individual indexing operations that will increase run time significantly.

Example code snippet

```bash
nohup psql -d {dbName} -f dbSchemas/openalex-pg-index.sql &
```

### Step 5: Create `openalex.abstracts` table

OpenAlex only contains an inverted index array of the abstracts. 
For search and readability, we want to recreate abstracts as accurately as possible. 
Run `transformData/openalex-abstract.sql` to create an `abstracts` table containing this information.

Example code snippet

```bash
nohup psql -d {dbName} -f transformData/openalex-abstract.sql
```

## Semantic Scholar

### Step 1: Extract Downloaded Archive

*todo: this step will become a download step in the future using `downloadData/download-semanticscholar.py`.*

Extract archive to `/semanticscholar/data/input/`.
If the save location is changed, it will also need to be changed in downstream scripts.
The folder should contain only `.jsonl` files named [`abstracts`,`authors`,`papers`,`s2orc`,`tldrs`].

### Step 2: Initialize Schema

Run `dbSchemas/semanticscholar-pg-schema.sql`.
The default schema name will be `s2`.

Example code snippet

```bash
nohup psql -d {dbName} -f dbSchemas/semanticscholar-pg-schema.sql
```

### Step 3: Populate Tables

Example code snippet

```bash
nohup psql -d {dbName} -f loadData/copy-semanticscholar.sql
```

### Step 4: Initialize Indexes

Example code snippet

```bash
nohup psql -d {dbName} -f dbSchemas/semanticscholar-pg-index.sql
```

## Core

### Step 1: Extract Downloaded Archive

Extract `*.tar.xz` into `/core/data/input/`. 
This will fill the directory with several thousand subsequent `{provider_id}.tar.xz`, 
each representing a provider for core.

Example code snippet

```bash
tar -xf core_archive.tar.xz -C core/data/input/
```

### Step 2: Convert Provider Archives and Separate Fulltext
*todo: even though it is parallelized, still pretty slow. Can I use the manifest?*

Run `transformData/unpack_core_parallel.sh`. 
If archives are in different location from default, modify the `ROOTPATH` variable.
It does the following:

* Iterate through `input`.
* Unpack the archives, separating `fulltext` from the rest of metadata.
* Repackage the metadata into one `.jsonl` per provider. 
* Add `provider_id` column.
* create a compressed archive of `fulltext`. 
* Delete the original `{provider_id}.tar.xz`.

Example code snippet

```bash
nohup bash unpack_core_parallel.sh &
```

### Step 3: Initialize Schema

Run `dbSchemas/core-pg-schema.sql`.

Example code snippet

```bash
nohup psql -d {dbName} -f dbSchemas/core-pg-schema.sql &
```

### Step 4: Populate Schema

Run `loadData/copy-core.sql`.

Example code snippet

```bash
nohup psql -d {dbName} -f loadData/copy-core.sql
```

### Step 5: Initialize Indexes

Run `dbSchemas/core-pg-index.sql`

Example code snippet

```bash
nohup psql -d {dbName} -f dbSchemas/core-pg-index.sql
```