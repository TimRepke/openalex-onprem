#!/usr/bin/env bash

# Set this to exit the script when an error occurs
set -e

# Remember where we are right now, later we might change to other places and want to find our way back
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Default variable values
config_file="secret.env"
sync_s3=false
run_solr=false
run_solr_clr=false
run_solr_res=false

run_pg_flat=false      # flatten postgres files
run_pg_drop_ind=false  # drop indices before import
run_pg_drop_dat=false  # drop selected data before import
run_pg_drop_full=false # drop all data before import
run_pg_import=false    # import data
run_pg_ind=false       # build indices
run_pg_clr=false       # drop tmp files

solr_skip_del="--skip-deletion"
pg_skip_del="--skip-deletion"

show_aws_progress=""   # set this to shut up aws progress in gitlab ci
override="--no-override"
preserve_ram="--preserve-ram"
jobs=1

with_sudo=""

# Function to display script usage
usage() {
 echo "Usage: $0 TMP_DIR [OPTIONS]"
 echo "   TMP_DIR is the absolute path to a directory where we can temporarily put files"
 echo "Options:"
 echo " --config FILE   .env config destination"
 echo " --sync          Sync OpenAlex S3 bucket"
 echo " --solr          Update Solr collection"
 echo " --solr-res      Reset solr index (start fresh)"
 echo " --solr-del      Delete deprecated data in solr"
 echo " --solr-clr      Clean temporary data (solr)"
 echo " --pg-del-ind    Drop all indices in postgres to speed up import"
 echo " --pg-del-dat    Drop all data from postgres before import"
 echo " --pg-del-upd    Drop only deprecated data from postgres before import"
 echo " --pg-flat       Flatten files for postgres"
 echo " --pg            Run postgres import"
 echo " --pg-ind        Create postgres indices"
 echo " --pg-clr        Clean temporary data (postgres)"
 echo " --override      Ignore existing flattened files and override them"
 echo " --jobs N        Number of processes for parallel processing"
 echo " --use-ram       Will not try to preserve RAM for small performance boost"
 echo " --no-progress   Set this to shut up aws sync updates (spams the gitlab-ci log)"
 echo " --with-sudo     Run some operations with sudo prefix"
 echo ""
 echo " -h, --help      Display this help message"
}

if [ $# -lt 1 ]; then
  usage
fi

# Fetch first parameter, as this is the working directory
tmp_dir=$1
shift
if [ ! -d "$tmp_dir" ]; then
  echo "The TMP_DIR='$tmp_dir' does not exist!"
  echo ""
  usage
  exit 1
fi

# Parse command-line arguments
while [ $# -gt 0 ]; do
  case $1 in
    -h | --help)
      usage
      exit 0
      ;;
    --config)
      shift
      config_file=$1
      ;;
    --sync)
      sync_s3=true
      ;;
    --solr)
      run_solr=true
      ;;
    --solr-res)
      run_solr_res=true
      ;;
    --solr-del)
      solr_skip_del="--no-skip-deletion"
      ;;
    --solr-clr)
      run_solr=true
      ;;
    --pg-del-ind)
      run_pg_drop_ind=true
      ;;
    --pg-del-dat)
      run_pg_drop_full=true
      pg_skip_del="--skip-deletion"
      ;;
    --pg-del-upd)
      pg_skip_del="--no-skip-deletion"
      run_pg_drop_dat=true
      ;;
    --pg-flat)
      run_pg_flat=true
      ;;
    --pg)
      run_pg_import=true
      ;;
    --pg-ind)
      run_pg_ind=true
      ;;
    --pg-clr)
      run_pg_clr=true
      ;;
    --override)
      override="--override"
      ;;
    --jobs)
      shift
      jobs=$1
      ;;
    --use-ram)
      preserve_ram="--no-preserve-ram"
      ;;
    --no-progress)
      show_aws_progress="--no-progress"
      ;;
    --with-sudo)
      with_sudo="sudo"
      ;;
    *)
      echo "Invalid option: $1" >&2
      usage
      exit 1
      ;;
  esac
  shift
done

export OA_CONFIG="${config_file}"

# Load config parameters from env file
# shellcheck source=default.env
source "${OA_CONFIG}"

do_compile() {
  DIR_PRE=$(pwd)
  # Go back to script directory
  cd "$SCRIPT_DIR" || exit
  # Load our python environment
  source ../venv/bin/activate || exit

  echo "Ensuring cython sources are compiled..."
  cd shared/cyth
  # Make sure cython stuff is compiled
  python setup.py build_ext --inplace

  # Go back and clear environment
  cd "$DIR_PRE"
  deactivate
}

# =======================================================
# S3 bucket sync
# =======================================================
echo "-=# (1/3) S3 bucket sync #=-"

LAST_SYNC=$([ -f "$OA_LAST_SYNC_FILE" ] && cat "$OA_LAST_SYNC_FILE" || echo "1970-01-01")
LAST_UPDT_PG=$([ -f "$OA_LAST_UPDATE_PG_FILE" ] && cat "$OA_LAST_UPDATE_PG_FILE" || echo "1970-01-01")
LAST_UPDT_SOLR=$([ -f "$OA_LAST_UPDATE_SOLR_FILE" ] && cat "$OA_LAST_UPDATE_SOLR_FILE" || echo "1970-01-01")
TODAY=$(date +%Y-%m-%d)

echo "Date for today: ${TODAY}"
echo "Last S2 sync: ${LAST_SYNC} (from ${OA_LAST_SYNC_FILE})"
echo "Last update: ${LAST_UPDT_PG} (from ${OA_LAST_UPDATE_PG_FILE})"
echo "Last update: ${LAST_UPDT_SOLR} (from ${OA_LAST_UPDATE_SOLR_FILE})"

if [ "$sync_s3" = true ] && [ "$TODAY" \> "$LAST_SYNC" ]; then
  echo "Syncing openalex S3 bucket..."
  # Go to snapshot directory
  cd "$OA_SNAPSHOT" || exit

  # Go one up again so that s3 can sync it
  cd ..

  # Commission S3 sync
  aws s3 sync "s3://openalex" "openalex-snapshot" --no-sign-request --delete "$show_aws_progress"

  # Update group to openalex, so that everyone can read it later
  $with_sudo chgrp -R openalex .
  $with_sudo chmod -R 775 .

  # Remember that we synced the snapshot
  rm -f "$OA_LAST_SYNC_FILE"
  echo "$TODAY" > "$OA_LAST_SYNC_FILE"
else
  echo "Assuming the OpenAlex snapshot is up to date, not syncing!"
fi


# =======================================================
# Solr
# =======================================================
echo "-=# (2/3) SOLR import #=-"

if [ "$run_solr_res" = true ]; then
  cd "$SCRIPT_DIR" || exit

  echo "Dropping solr collection..."
  "${OA_SOLR_BIN}/solr" delete -c "$OA_SOLR_COLLECTION" -p "$OA_SOLR_PORT"  || echo "Collection '$OA_SOLR_COLLECTION' did not exist!"

  echo "Creating empty solr collection..."
  "${OA_SOLR_BIN}/solr" zk cp file:setup/managed-schema.xml zk:/configs/._designer_openalex/managed-schema.xml -z "$OA_SOLR_HOST:$OA_SOLR_ZOO"
  "${OA_SOLR_BIN}/solr" create -c "$OA_SOLR_COLLECTION" -n "._designer_openalex" -p "$OA_SOLR_PORT"
else
  echo "Keeping existing index untouched."
fi

if [ "$run_solr" = true ]; then
  # Go back to the script directory
  cd "$SCRIPT_DIR" || exit

  # Make sure code is compiled
  do_compile

  # Load our python environment
  source ../venv/bin/activate

  echo "Running solr import..."
  python update_solr.py "$solr_skip_del" --loglevel INFO "$tmp_dir/solr"

  # Leave python environment
  deactivate

  # Remember that we synced the snapshot
  rm -f "$OA_LAST_UPDATE_SOLR_FILE"
  echo "$TODAY" > "$OA_LAST_UPDATE_SOLR_FILE"
fi

if [ "$run_solr_clr" = true ]; then
  echo "Clearing $tmp_dir/solr"
  rm -r "$tmp_dir/solr"
else
  echo "Leaving $tmp_dir/solr untouched"
fi


# =======================================================
# Postgres
# =======================================================
echo "-=# (3/3) Postgres import #=-"

# shellcheck disable=SC2034
export PGPASSWORD="$OA_PG_PW"  # set for passwordless postgres

if [ "$run_pg_flat" = true ]; then
  # Go back to the script directory
  cd "$SCRIPT_DIR" || exit

  # Make sure code is compiled
  do_compile

  # Load our python environment
  source ../venv/bin/activate

  echo "Flattening files for postgres"
  python update_postgres.py --loglevel INFO --parallelism "$jobs" "$preserve_ram" "$pg_skip_del" "$override" "$tmp_dir/postgres"

  # Leave python environment
  deactivate
fi

if [ "$run_pg_drop_ind" = true ]; then
  echo "Dropping indexes to speed up imports..."
  cd "$SCRIPT_DIR" || exit
  psql -f ./setup/pg_indices_drop.sql -p "$OA_PG_PORT" -h "$OA_PG_HOST" -U "$OA_PG_USER" --echo-all -d "$OA_PG_DB"
fi

if [ "$run_pg_drop_full" = true ]; then
  echo "Dropping all data from the database..."
  cd "$SCRIPT_DIR" || exit
  psql -f ./setup/pg_clear.sql -p "$OA_PG_PORT" -h "$OA_PG_HOST" -U "$OA_PG_USER" --echo-all -d "$OA_PG_DB"
elif [ "$run_pg_drop_dat" = true ]; then
  echo "Deleting merged objects..."
  cd "$tmp_dir" || exit
  find ./postgres -name "*-merged_del.sql" -exec psql -f {} -p "$OA_PG_PORT" -h "$OA_PG_HOST" -U "$OA_PG_USER" --echo-all -d "$OA_PG_DB" \;
  echo "Deleting existing new objects..."
  find ./postgres -name "*-del.sql" -exec psql -f {} -p "$OA_PG_PORT" -h "$OA_PG_HOST" -U "$OA_PG_USER" --echo-all -d "$OA_PG_DB" \;
fi

if [ "$run_pg_import" = true ]; then
  echo "Import new or updated objects"
  cd "$tmp_dir" || exit
  find ./postgres -name "*-cpy.sql" -exec psql -f {} -p "$OA_PG_PORT" -h "$OA_PG_HOST" -U "$OA_PG_USER" --echo-all -d "$OA_PG_DB" \;

  # Remember that we synced the snapshot
  rm -f "$OA_LAST_UPDATE_PG_FILE"
  echo "$TODAY" > "$OA_LAST_UPDATE_PG_FILE"
fi

if [ "$run_pg_ind" = true ]; then
  echo "Creating indexes again..."
  cd "$SCRIPT_DIR" || exit
  psql -f ./setup/pg_indices.sql -p "$OA_PG_PORT" -h "$OA_PG_HOST" -U "$OA_PG_USER" --echo-all -d "$OA_PG_DB"
fi

if [ "$run_pg_clr" = true ]; then
  echo "Deleting all temporary flattened files and scripts"
  rm -r "$tmp_dir/postgres"
fi


echo "All updates done!"
echo "Remember to update the date in $OA_LAST_UPDTAE_FILE"