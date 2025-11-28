#!/usr/bin/env bash

# Set this to exit the script when an error occurs
set -e
# Set this to print commands before executing
set -o xtrace

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR
source b.env

echo $A
echo $B