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
 echo ""
 echo " -h, --help          Display this help message"
}

if [ $# -lt 2 ]; then
  usage
  exit 1
fi

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

cd "${SCRIPT_DIR}"
cd ../solr
echo $(pwd)

echo "-=# SOLR setup #=-"

echo "Solr at $NACSOS_OPENALEX__SOLR_HOST:$NACSOS_OPENALEX__SOLR_PORT/$NACSOS_OPENALEX__SOLR_COLLECTION (zoo at $NACSOS_OPENALEX__SOLR_ZOO_PORT)"
echo "  - Binaries: $NACSOS_OPENALEX__SOLR_BIN"
echo "  - Home: $NACSOS_OPENALEX__SOLR_HOME"

echo "Making sure solr instance is running..."
"${OA_SOLR_BIN}/solr" stop -p "$NACSOS_OPENALEX__SOLR_PORT" -h "$NACSOS_OPENALEX__SOLR_BIN" || echo "Tried to stop solr, but wasn't running"
"${OA_SOLR_BIN}/solr" start -c -p "$NACSOS_OPENALEX__SOLR_PORT" -s "$NACSOS_OPENALEX__SOLR_HOME" -h "$NACSOS_OPENALEX__SOLR_BIN"

echo "Dropping solr collection..."
"${OA_SOLR_BIN}/solr" delete -c "$NACSOS_OPENALEX__SOLR_COLLECTION" -p "$NACSOS_OPENALEX__SOLR_PORT"  || echo "Collection '$NACSOS_OPENALEX__SOLR_COLLECTION' did not exist!"

echo "Creating empty solr collection..."
"${OA_SOLR_BIN}/solr" zk upconfig -d "solr_configset" -n _openalex_conf -z "$NACSOS_OPENALEX__SOLR_BIN:$NACSOS_OPENALEX__SOLR_ZOO_PORTO"
"${OA_SOLR_BIN}/solr" create -c "$NACSOS_OPENALEX__SOLR_COLLECTION" -n _openalex_conf -p "$NACSOS_OPENALEX__SOLR_PORT"

echo "Waiting a bit..."
sleep 5
echo "Finished."
