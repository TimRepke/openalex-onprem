#!/usr/bin/env bash

# Set this to exit the script when an error occurs
set -e
# Set this to print commands before executing
set -o xtrace


# Absolute path to this script directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Function to display script usage
usage() {
 echo "Usage: $0 [OPTIONS]"
 echo ""
 echo "Options:"
 echo " --config FILE       .env config destination"
 echo " --from              Only include partitions after date"
 echo " --skip              Skip first n partitions"
 echo " --batchsize         How many items to post at once to solr"
 echo ""
 echo " -h, --help          Display this help message"
}

if [ $# -lt 2 ]; then
  usage
  exit 1
fi

bs=50000
skip=0
from_dt="1970-01-01"
config_file=

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
    --from)
      shift
      from_dt=$1
      ;;
    --skip)
      shift
      skip=$1
      ;;
    --batchsize)
      shift
      bs=$1
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

export UV_PROJECT_ENVIRONMENT=.venv
export NACSOS_CONFIG="${config_file}"
source "${NACSOS_CONFIG}"

# Ensure correct working directory
cd "${SCRIPT_DIR}"
cd ../..
echo $(pwd)

if [ -f ".venv" ]; then
  source .venv/bin/activate
else
  python3.13 -m venv .venv
  source .venv/bin/activate
  pip install uv
fi
uv sync --active

echo "-=# Load snapshot into solr #=-"
python snapshot/load.py --snapshot="$NACSOS_OPENALEX__SNAPSHOT_DIR" \
                        --config-file="$config_file" \
                        --skip-n-partitions="$skip" \
                        --filter-since="$from_dt" \
                        --loglevel=INFO \
                        --post-batchsize="$bs"

deactivate

echo "Yay, done!"
