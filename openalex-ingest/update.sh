#!/usr/bin/env bash

# Set this to exit the script when an error occurs
set -e

# Default variable values
sync_s3=true
compile=true
update_solr=true
update_pg=true
cleanup=true
jobs=1
del_prior=""

# Function to display script usage
usage() {
 echo "Usage: $0 TMP_DIR [OPTIONS]"
 echo "   TMP_DIR is the absolute path to a directory where we can temporarily put files"
 echo "Options:"
 echo " --skip-sync     Skip synchronisation with OpenAlex S3 bucket"
 echo " --skip-compile  Skip (re-)compilation of Cython code"
 echo " --skip-solr     Skip update of Solr collection"
 echo " --skip-pg       Skip update of postgres"
 echo " --skip-del      Skip deletion of existing data in db/solr"
 echo " --skip-clean    Skip deleting all temporary files"
 echo " --jobs N        Number of processes for parallel processing"
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
    --skip-sync)
      sync_s3=false
      ;;
    --skip-compile)
      compile=false
      ;;
    --skip-solr)
      update_solr=false
      ;;
    --skip-pg)
      update_pg=false
      ;;
    --skip-del)
      del_prior="--skip-deletion"
      ;;
    --skip-clean)
      cleanup=false
      ;;
    --jobs)
      shift
      jobs=$1
      ;;
    *)
      echo "Invalid option: $1" >&2
      usage
      exit 1
      ;;
  esac
  shift
done

# Remember where we are right now, later we might change to other places and want to find our way back
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export OA_CONFIG="secret.env"

# Load config parameters from env file
# shellcheck source=default.env
source "${OA_CONFIG}"

if [ "$sync_s3" = true ]; then
  echo "Syncing openalex S3 bucket..."
  # Go to snapshot directory
  cd "$OA_SNAPSHOT" || exit
  # Go one up again so that s3 can sync it
  cd ..
  # Commission S3 sync
  aws s3 sync "s3://openalex" "openalex-snapshot" --no-sign-request
  # Update group to openalex, so that everyone can read it later
  chgrp -R openalex .
  chmod -R 775 .
else
  echo "Assuming the OpenAlex snapshot is up to date, not syncing!"
fi

# Go back to script directory
cd "$SCRIPT_DIR" || exit

# Load our python environment
source ../venv/bin/activate

if [ "$compile" = true ]; then
  echo "Ensuring cython sources are compiled..."
  cd shared/cyth
  # Make sure cython stuff is compiled
  python setup.py build_ext --inplace
  cd ../..
fi

if [ "$update_solr" = true ]; then
  echo "Updating solr..."
  python update_solr.py "$del_prior" --loglevel INFO "$tmp_dir/solr"
  echo "Clearing $tmp_dir/solr"
  rm -r "$tmp_dir/solr"
else
  echo "Skipping update of Solr collection!"
fi

if [ "$update_pg" = true ]; then
  echo "Updating PostgreSQL..."
  python update_postgres.py "$del_prior" --loglevel INFO "$tmp_dir/postgres" --parallelism "$jobs"

  cd "$tmp_dir"
  if [ "$del_prior" = "--skip-deletion" ]; then
    echo "Deleting merged objects"
    psql -f postgres/*merged_del.sql
    echo "Deleting existing new objects"
    psql -f postgres/*-del.sql
  fi
  echo "Import new or updated objects"
  psql -f postgres/*-cpy.sql

  if [ "$cleanup" = true ]; then
    echo "Deleting all temporary flattened files and scripts"
    rm -r "$tmp_dir/postgres"
  fi

  cd "$SCRIPT_DIR"
else
  echo "Skipping update of Postgres database!"
fi

echo "All updates done!"
echo "Remember to update the date in $OA_LAST_UPDTAE_FILE"