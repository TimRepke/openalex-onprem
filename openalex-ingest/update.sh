#!/usr/bin/env bash

# Set this to exit the script when an error occurs
set -e

# Remember where we are right now, later we might change to other places and want to find our way back
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Default variable values
config_file="secret.env"
sync_s3=false
run_solr=false
run_solr_import=false
run_solr_import_full=false
run_solr_tmp=false
run_solr_clr=false
run_solr_res=false
run_solr_swp=false

run_pg=false
run_pg_flat=false      # flatten postgres files
run_pg_drop_ind=false  # drop indices before import
run_pg_drop_dat=false  # drop selected data before import
run_pg_drop_full=false # drop all data before import
run_pg_import=false    # import data
run_pg_ind=false       # build indices
run_pg_clr=false       # drop tmp files
run_pg_tmp=false       # Spin up pg cluster

solr_skip_del="--skip-deletion"
pg_skip_del="--skip-deletion"

show_aws_progress=""   # set this to shut up aws progress in gitlab ci
override="--no-override"
preserve_ram="--preserve-ram"
jobs=1

with_sudo=""
with_tmp=false

# Function to display script usage
usage() {
 echo "Usage: $0 [OPTIONS]"
 echo ""
 echo "Options:"
 echo " --config FILE       .env config destination"
 echo ""
 echo " --sync              Sync OpenAlex S3 bucket"
 echo ""
 echo " --solr              Run solr-related tasks"
 echo " --solr-import       Update Solr collection"
 echo " --solr-import-full  Do that update from scratch (i.e. not skipping partitions)"
 echo " --solr-tmp          Spin up temporary solr instance for import"
 echo " --solr-swp          Shut down temporary solr instance and transfer solr-home"
 echo " --solr-res          Reset solr index (start fresh)"
 echo " --solr-del          Delete deprecated data in solr"
 echo " --solr-clr          Clean temporary data (solr)"
 echo ""
 echo " --pg                Run postgres-related tasks"
 echo " --pg-del-ind        Drop all indices in postgres to speed up import"
 echo " --pg-del-dat        Drop all data from postgres before import"
 echo " --pg-del-upd        Drop only deprecated data from postgres before import"
 echo " --pg-flat           Flatten files for postgres"
 echo " --pg-import         Run postgres import"
 echo " --pg-tmp            Spin up temporary PG cluster for import"
 echo " --pg-ind            Create postgres indices"
 echo " --pg-clr            Clean temporary data (postgres)"
 echo " --override          Ignore existing flattened files and override them"
 echo " --jobs N            Number of processes for parallel processing"
 echo " --use-ram           Will not try to preserve RAM for small performance boost"
 echo " --no-progress       Set this to shut up aws sync updates (spams the gitlab-ci log)"
 echo " --with-sudo         Run some operations with sudo prefix"
 echo " --with-tmp          Use tmp parameters where possible"
 echo ""
 echo " -h, --help          Display this help message"
}

if [ $# -lt 2 ]; then
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
    --pg)
      run_pg=true
      ;;
    --solr-import)
      run_solr_import=true
      ;;
    --solr-import-full)
      run_solr_import_full=true
      ;;
    --solr-tmp)
      with_tmp=true
      run_solr_tmp=true
      ;;
    --solr-swp)
      run_solr_swp=true
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
    --pg-import)
      run_pg_import=true
      ;;
    --pg-ind)
      run_pg_ind=true
      ;;
    --pg-clr)
      run_pg_clr=true
      ;;
    --pg-tmp)
      run_pg_tmp=true
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
    --with-tmp)
      with_tmp=true
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


if [ ! -d "$OA_TMP_DIR" ]; then
  echo "The TMP_DIR='$OA_TMP_DIR' does not exist!"
  echo ""
  usage
  exit 1
fi


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

LAST_SYNC=$([ -f "$OA_LAST_SYNC_FILE" ] && cat "$OA_LAST_SYNC_FILE" || echo "1970-01-01")
LAST_UPDT_PG=$([ -f "$OA_LAST_UPDATE_PG_FILE" ] && cat "$OA_LAST_UPDATE_PG_FILE" || echo "1970-01-01")
LAST_UPDT_SOLR=$([ -f "$OA_LAST_UPDATE_SOLR_FILE" ] && cat "$OA_LAST_UPDATE_SOLR_FILE" || echo "1970-01-01")
TODAY=$(date +%Y-%m-%d)

echo "Date for today: ${TODAY}"
echo "Last S2 sync: ${LAST_SYNC} (from ${OA_LAST_SYNC_FILE})"
echo "Last update: ${LAST_UPDT_PG} (from ${OA_LAST_UPDATE_PG_FILE})"
echo "Last update: ${LAST_UPDT_SOLR} (from ${OA_LAST_UPDATE_SOLR_FILE})"

# =======================================================
# S3 bucket sync
# =======================================================
echo "-=# S3 bucket sync #=-"

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


if [ "$run_solr" = true ]; then
  # =======================================================
  # Solr
  # =======================================================
  echo "-=# SOLR import #=-"
  
  if [ "$with_tmp" = true ]; then
    echo "Going to use tmp connection info"
    OA_SOLR_BIN="${OA_SOLR_BIN_TMP}"
    OA_SOLR_HOME="${OA_SOLR_HOME_TMP}"
    OA_SOLR_HOST="${OA_SOLR_HOST_TMP}"
    OA_SOLR_PORT="${OA_SOLR_PORT_TMP}"
    OA_SOLR_ZOO="${OA_SOLR_ZOO_TMP}"
  else
    echo "Going to use production connection info"
    OA_SOLR_BIN="${OA_SOLR_BIN_PROD}"
    OA_SOLR_HOME="${OA_SOLR_HOME_PROD}"
    OA_SOLR_HOST="${OA_SOLR_HOST_PROD}"
    OA_SOLR_PORT="${OA_SOLR_PORT_PROD}"
    OA_SOLR_ZOO="${OA_SOLR_ZOO_PROD}"
  fi
  echo "Solr at $OA_SOLR_HOST:$OA_SOLR_PORT/$OA_SOLR_COLLECTION (zoo at $OA_SOLR_ZOO)"
  echo "  - Binaries: $OA_SOLR_BIN"
  echo "  - Home: $OA_SOLR_HOME"

  if [ "$run_solr_tmp" = true ]; then
    cd "$SCRIPT_DIR" || exit

    echo "Prepping secondary solr instance at port ${OA_SOLR_PORT_TMP}"
    echo "  - Using solr binaries at: ${OA_SOLR_BIN_TMP}"
    echo "  - Production solr-home: ${OA_SOLR_HOME_PROD}"
    echo "  - Temporary solr-home: ${OA_SOLR_HOME_TMP}"

    echo "Making sure tmp solr instance is running..."
    "${OA_SOLR_BIN}/solr" start -c -p "$OA_SOLR_BIN_TMP"

    echo "Dropping solr collection..."
    "${OA_SOLR_BIN}/solr" delete -c "$OA_SOLR_COLLECTION" -p "$OA_SOLR_BIN_TMP"  || echo "Collection '$OA_SOLR_COLLECTION' did not exist!"

    echo "Creating empty solr collection..."
    "${OA_SOLR_BIN}/solr" zk upconfig -d setup/solr_configset -n _openalex_conf -z "$OA_SOLR_HOST_TMP:$OA_SOLR_ZOO_TMP"
    "${OA_SOLR_BIN}/solr" create -c "$OA_SOLR_COLLECTION" -n _openalex_conf -p "$OA_SOLR_PORT_TMP"

    echo "Waiting a bit..."
    sleep 5
  fi

  if [ "$run_solr_res" = true ]; then
    cd "$SCRIPT_DIR" || exit

    echo "Dropping solr collection..."
    "${OA_SOLR_BIN}/solr" delete -c "$OA_SOLR_COLLECTION" -p "$OA_SOLR_PORT"  || echo "Collection '$OA_SOLR_COLLECTION' did not exist!"

    echo "Creating empty solr collection..."
    # "${OA_SOLR_BIN}/solr" zk cp file:setup/solr_managed-schema.xml zk:/configs/._designer_openalex/managed-schema.xml -z "$OA_SOLR_HOST:$OA_SOLR_ZOO"
    # "${OA_SOLR_BIN}/solr" create -c "$OA_SOLR_COLLECTION" -d setup/solr_configset -n openalex_conf -p "$OA_SOLR_PORT"
    "${OA_SOLR_BIN}/solr" zk upconfig -d setup/solr_configset -n _openalex_conf -z "$OA_SOLR_HOST:$OA_SOLR_ZOO"
    "${OA_SOLR_BIN}/solr" create -c "$OA_SOLR_COLLECTION" -n _openalex_conf -p "$OA_SOLR_PORT"

    echo "Waiting a bit..."
    sleep 5
  else
    echo "Keeping existing index untouched."
  fi

  if [ "$run_solr_import" = true ]; then
    # Go back to the script directory
    cd "$SCRIPT_DIR" || exit

    # Make sure code is compiled
    do_compile

    # Load our python environment
    source ../venv/bin/activate

    if [ "$run_solr_import_full" = true ]; then
      LAST_UP="1970-01-01"
    else
      LAST_UP="$LAST_UPDT_SOLR"
    fi

    echo "Running solr import..."
    python update_solr.py --tmp-dir="$OA_TMP_DIR/solr" \
                          --snapshot-dir="$OA_SNAPSHOT" \
                          --solr-collection="$OA_SOLR_COLLECTION" \
                          --solr-host="$OA_SOLR_HOST" \
                          --solr-port="$OA_SOLR_PORT" \
                          --last-solr-update="$LAST_UP" \
                          "$solr_skip_del" --loglevel=INFO

    # Leave python environment
    deactivate

    # Remember that we synced the snapshot
    rm -f "$OA_LAST_UPDATE_SOLR_FILE"
    echo "$TODAY" > "$OA_LAST_UPDATE_SOLR_FILE"
  fi

  if [ "$run_solr_clr" = true ]; then
    echo "Clearing $OA_TMP_DIR/solr"
    rm -r "$OA_TMP_DIR/solr"
  else
    echo "Leaving $OA_TMP_DIR/solr untouched"
  fi

  if [ "$run_solr_swp" = true ]; then
    echo "Transferring data from secondary solr instance to production"
    echo "  - Using production solr binaries at: ${OA_SOLR_BIN_PROD}"
    echo "  - Using secondary solr binaries at: ${OA_SOLR_BIN_TMP}"
    echo "  - Production solr-home: ${OA_SOLR_HOME_PROD}"
    echo "  - Temporary solr-home: ${OA_SOLR_HOME_TMP}"

    echo "Shutting down solr instances as to not confuse them too much"
    "${OA_SOLR_BIN_TMP}/solr" stop -p "$OA_OA_SOLR_PORT_TMP"
    "${OA_SOLR_BIN_PROD}/solr" stop -p "$OA_OA_SOLR_PORT_PROD"

    echo "Copying solr-home folders"
    rm -r "$OA_SOLR_HOME_PROD"
    cp -r "$OA_SOLR_HOME_TMP/*" "$OA_SOLR_HOME_PROD"
    $with_sudo chown -R solr:solr "$OA_SOLR_HOME_PROD"

    echo "Making sure tmp solr instance is running..."
    # FIXME: move all settings to solr.in.sh
    sudo -u solr "${OA_SOLR_BIN_PROD}/solr" start -c -h "$OA_SOLR_HOST_PROD" -m 20g -s "$OA_SOLR_HOME_PROD" -Denable.packages=true -Dsolr.modules=sql,clustering -Dsolr.max.booleanClauses=4096

    echo "NOTE: not deleting the temporary solr-home at ${OA_SOLR_HOME_TMP}"
  fi
fi


if [ "$run_pg" = true ]; then
  # =======================================================
  # Postgres
  # =======================================================
  echo "-=# Postgres import #=-"

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
    python update_postgres.py --loglevel INFO --parallelism "$jobs" "$preserve_ram" "$pg_skip_del" "$override" "$OA_TMP_DIR/postgres"

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
    cd "$OA_TMP_DIR" || exit
    find ./postgres -name "*-merged_del.sql" -exec psql -f {} -p "$OA_PG_PORT" -h "$OA_PG_HOST" -U "$OA_PG_USER" --echo-all -d "$OA_PG_DB" \;
    echo "Deleting existing new objects..."
    find ./postgres -name "*-del.sql" -exec psql -f {} -p "$OA_PG_PORT" -h "$OA_PG_HOST" -U "$OA_PG_USER" --echo-all -d "$OA_PG_DB" \;
  fi

  if [ "$run_pg_tmp" = true ]; then
    echo "Spinning up temporary PG cluster..."
    pg_createcluster 16 oaimport -p 5434 -d "${pg_tmp_data}" --start
    # create schema
    # create users
    # grant permissions
    # [run import]
    # [build indices]
    # sudo pg_dropcluster 16 main
    # sudo systemctl stop postgresql
    # Drop old directory
    # sudo rm /var/lib/postgresql/16/main
    # Move new directory
    # sudo mv "${pg_tmp_data}" /var/lib/postgresql/16/main
    # edit /etc/postgresql/14/main/postgresql.conf
    #    -> data_directory = '/var/lib/postgresql/16/main'
    # sudo pg_dropcluster 16 oaimport
    # start service again
  fi

  if [ "$run_pg_import" = true ]; then
    echo "Import new or updated objects"
    cd "$OA_TMP_DIR" || exit
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
    rm -r "$OA_TMP_DIR/postgres"
  fi
fi

echo "Script finished!"