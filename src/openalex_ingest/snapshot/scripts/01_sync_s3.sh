#!/usr/bin/env bash

# Set this to exit the script when an error occurs
set -e
# Set this to print commands before executing
set -o xtrace


# Function to display script usage
usage() {
 echo "Usage: $0 [OPTIONS]"
 echo ""
 echo "Options:"
 echo " --config FILE       .env config destination"
 echo " --no-progress       Set this to shut up aws sync updates (spams the gitlab-ci log)"
 echo " --with-sudo         Run some operations with sudo prefix"
 echo ""
 echo " -h, --help          Display this help message"
}

if [ $# -lt 2 ]; then
  usage
  exit 1
fi

show_aws_progress=""
with_sudo=""

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

if [[ -z "$config_file" ]]; then
  echo "No .env specified!"
  exit 1
fi

export NACSOS_CONFIG="${config_file}"
source "${NACSOS_CONFIG}"

echo "-=# S3 bucket sync #=-"

echo "Syncing openalex S3 bucket..."
# Go to snapshot directory
cd "$NACSOS_OPENALEX__SNAPSHOT_DIR" || exit

# Go one up again so that s3 can sync it
cd ..

# Commission S3 sync
aws s3 sync "s3://openalex/data" "openalex-snapshot/data" --no-sign-request --delete "$show_aws_progress"

# Update group to openalex, so that everyone can read it later
$with_sudo chgrp -R openalex "$NACSOS_OPENALEX__SNAPSHOT_DIR"
$with_sudo chmod -R 775 "$NACSOS_OPENALEX__SNAPSHOT_DIR"

echo "All synced up."
