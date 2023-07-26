#!/usr/bin/env bash

# Default variable values
sync_s3=true
compile=true
update_solr=true
update_pg=true

# Function to display script usage
usage() {
 echo "Usage: $0 [OPTIONS]"
 echo "Options:"
 echo " --skip-sync     Skip synchronisation with OpenAlex S3 bucket"
 echo " --skip-compile  Skip (re-)compilation of Cython code"
 echo " --skip-solr     Skip update of Solr collection"
 echo " --skip-pg       Skip update of postgres"
 echo ""
 echo " -h, --help      Display this help message"
}

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

# Load config parameters from env file
source secret.env

if [ "$sync_s3" = true ]; then
  echo "Syncing openalex S3 bucket..."
  # Go to snapshot directory
  cd "$OA_SNAPSHOT" || exit
  # Go one up again so that s3 can sync it
  cd ..
  # Commission S3 sync
  aws s3 sync "s3://openalex" "openalex-snapshot" --no-sign-request
  # Update group to openalex, so that eveyone can read it later
  chgrp -R openalex .
else
  echo "Assuming the OpenAlex snapshot is up to date, not syncing!"
fi

# Go back to script directory
cd "$SCRIPT_DIR" || exit

# Load our python environment
source venv/bin/activate

if [ "$compile" = true ]; then
  echo "Ensuring cython sources are compiled..."
  # Make sure cython stuff is compiled
  python setup.py build_ext --inplace
fi

if [ "$update_solr" = true ]; then
  echo "Updating solr..."
  python update_solr.py
else
  echo "Skipping update of Solr collection!"
fi

if [ "$update_pg" = true ]; then
  echo "Updating PostgreSQL..."
#  python update_postgres.py
  echo " -xxx- Skipped for now, not implemented yet! -xxx-"
else
  echo "Skipping update of Postgres database!"
fi

echo "All updates done!"
echo "Remember to update the date in $OA_LAST_UPDTAE_FILE"