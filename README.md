# About This Folder

This contains all relevant scripts for ETL work for MCC's postgresDB. Files are organized by their usage and labelled by the appropriate DB.
Eventually these will all be streamlined into one set of scripts to run.


## OpenAlex

These steps are copied (more or less) from OpenAlex's documentation. To understand how to download the data
and for more detailed instructions on how to upload it to the postgres DB, please see [here](https://docs.openalex.org/download-snapshot)

####  Step 1 

Initialize Schema by running dbSchemas/openalex-pg-schema.sql

Example
```bash
psql -d db_name -f openalex-pg-schema.sql
```

#### Step 2

Convert JSON Files to flat CSV

Run flatten-openalex-jsonl.py. This script assumes that you are reading from file './openalex-snapshot'
and want to write into './csv-files'. Can be changed in the script (but will need to be changed for subsequent
scripts). This could potentially take several hours so best to run it in nohup.

*HINT*: by copying the script you can run conversions in parallel which could reduce the time to complete. This
can be done by commenting out the functions in the __main__() function at the bottom of the script. Then simply
run the scripts simultaneously.

Example
```bash
nohup python3 flatten-openalex-jsonl.py &
```

#### Step 3

Load flat CSVs to Database

Run copy-openalex-csv.sql to copy each csv-file subfolder into the appropriate table. This assumes that
you are running it from the folder directly above the csv-files/ subfolder. If you changed the name you
will have to change the location in each instance of the copy script. If you are loading e.g. works objects
it will take several hours and so it is *HIGHLY* recommended to nohup it.

Example
```bash
nohup psql -d db_name < copy-openalex.sql &
```

## Semantic Scholar

#### Step 1

Initialize Schema by running dbSchemas/semanticscholar-pg-schema.sql

Example
```bash
nohup psql -d db_name -f dbSchemas/semanticscholar-pg.schema.sql &
```
#### Step 2

Combine downloaded files into jsonl files

```bash
cat * > table_name.jsonl
```

#### Step 3

Load JSONL Files to DB

Run loadData/copy-semanticscholar.sql to load jsonl files into the database. This will take several hours and
so it is *HIGHLY* recommended to nohup it. The current iteration assumes jsonl are in location `/var/data/semanticscholar/local/data/json_outpus/`

```bash
nohup psql -d db_name -f loadData/copy-semanticscholar.sql &
```

## Core

#### Step 1

WIP
