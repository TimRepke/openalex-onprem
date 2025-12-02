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
cd ..
echo $(pwd)

echo "-=# SOLR setup #=-"

echo "Solr at $NACSOS_OPENALEX__SOLR_HOST:$NACSOS_OPENALEX__SOLR_PORT/$NACSOS_OPENALEX__SOLR_COLLECTION (zoo at $NACSOS_OPENALEX__SOLR_ZOO_PORT)"
echo "  - Binaries: $NACSOS_OPENALEX__SOLR_BIN"
echo "  - Home: $NACSOS_OPENALEX__SOLR_HOME"

echo "Making sure solr instance is running..."
"${NACSOS_OPENALEX__SOLR_BIN}/solr" stop --port "$NACSOS_OPENALEX__SOLR_PORT" --host "$NACSOS_OPENALEX__SOLR_HOST" || echo "Tried to stop solr, but wasn't running"
#rm -rf $NACSOS_OPENALEX__SOLR_HOME
#mkdir -p $NACSOS_OPENALEX__SOLR_HOME/data
"${NACSOS_OPENALEX__SOLR_BIN}/solr" start -c --host "$NACSOS_OPENALEX__SOLR_HOST" --port "$NACSOS_OPENALEX__SOLR_PORT" --memory 2g -Denable.packages=true -Dsolr.modules=sql,clustering -Dsolr.max.booleanClauses=4096 --solr-home "$NACSOS_OPENALEX__SOLR_HOME"

echo "Dropping solr collection..."
"${NACSOS_OPENALEX__SOLR_BIN}/solr" delete --name "$NACSOS_OPENALEX__SOLR_COLLECTION" -f --solr-url "http://$NACSOS_OPENALEX__SOLR_HOST:$NACSOS_OPENALEX__SOLR_PORT"  || echo "Collection '$NACSOS_OPENALEX__SOLR_COLLECTION' did not exist!"

echo "Creating empty solr collection..."
"${NACSOS_OPENALEX__SOLR_BIN}/solr" zk upconfig --conf-dir "solr/solr_configset" --conf-name openalex_schema --solr-url "http://$NACSOS_OPENALEX__SOLR_HOST:$NACSOS_OPENALEX__SOLR_ZOO_PORT"
"${NACSOS_OPENALEX__SOLR_BIN}/solr" create --name "$NACSOS_OPENALEX__SOLR_COLLECTION" --conf-dir "solr/solr_configset" --conf-name openalex_schema --solr-url "http://$NACSOS_OPENALEX__SOLR_HOST:$NACSOS_OPENALEX__SOLR_ZOO_PORT"

echo "Waiting a bit..."
sleep 5
echo "Finished."
