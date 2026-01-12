#!/usr/bin/env bash

# Set this to exit the script when an error occurs
set -e
# Set this to print commands before executing
set -o xtrace

# Absolute path to this script directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
USR_SELF=$(whoami)
USR_SOLR="solr"

# Function to display script usage
usage() {
 echo "Usage: $0 [OPTIONS]"
 echo ""
 echo "Options:"
 echo " --temp-config FILE       .env config destination for tmp instance"
 echo " --prod-config FILE       .env config destination for prod instance"
 echo ""
 echo " -h, --help          Display this help message"
}

if [ $# -lt 2 ]; then
  usage
  exit 1
fi

temp_conf=
prod_conf=

# Parse command-line arguments
while [ $# -gt 0 ]; do
  case $1 in
    -h | --help)
      usage
      exit 0
      ;;
    --temp-config)
      shift
      temp_conf=$1
      ;;
    --prod-config)
      shift
      prod_conf=$1
      ;;
    *)
      echo "Invalid option: $1" >&2
      usage
      exit 1
      ;;
  esac
  shift
done

if [[ -z "temp_conf" ]]; then
  echo "No .env specified!"
  exit 1
fi
if [[ -z "prod_conf" ]]; then
  echo "No .env specified!"
  exit 1
fi

source "${temp_conf}"
OA_SOLR_BIN_TMP=NACSOS_OPENALEX__SOLR_BIN
OA_SOLR_HOME_TMP=NACSOS_OPENALEX__SOLR_HOME
OA_SOLR_PORT_TMP=NACSOS_OPENALEX__SOLR_PORT

source "${prod_conf}"
OA_SOLR_BIN_PROD=NACSOS_OPENALEX__SOLR_BIN
OA_SOLR_HOME_PROD=NACSOS_OPENALEX__SOLR_HOME

echo "Transferring data from secondary solr instance to production"
echo "  - Using production solr binaries at: ${OA_SOLR_BIN_PROD}"
echo "  - Using secondary solr binaries at: ${OA_SOLR_BIN_TMP}"
echo "  - Production solr-home: ${OA_SOLR_HOME_PROD}"
echo "  - Temporary solr-home: ${OA_SOLR_HOME_TMP}"

echo "Shutting down solr instances as to not confuse them too much"
"${OA_SOLR_BIN_TMP}/solr"  stop -p "$OA_SOLR_PORT_TMP" || echo "Temporary solr instance was already down."
$with_sudo /usr/bin/systemctl stop solr.service

echo "Copying solr-home folders"
$with_sudo chown -R "$USR_SELF:$USR_SELF" "$OA_SOLR_HOME_PROD"
$with_sudo chown -R "$USR_SELF:$USR_SELF" "$OA_SOLR_HOME_TMP"
#rm -r "$OA_SOLR_HOME_PROD"/* || echo "solr home at '$OA_SOLR_HOME_PROD' already cleared."
mv "$OA_SOLR_HOME_PROD" "${OA_SOLR_HOME_PROD}_bak"
cp -r "$OA_SOLR_HOME_TMP"/* "$OA_SOLR_HOME_PROD"
$with_sudo chown -R "$USR_SOLR:$USR_SOLR" "$OA_SOLR_HOME_PROD"

echo "Starting up production solr again..."
$with_sudo /usr/bin/systemctl start solr.service

echo "NOTE: not deleting the temporary solr-home at ${OA_SOLR_HOME_TMP}"

# TODO: fix auth?
