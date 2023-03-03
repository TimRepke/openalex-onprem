#!/bin/bash

secs_to_human() {
    if [[ -z ${1} || ${1} -lt 60 ]] ;then
        min=0 ; secs="${1}"
    else
        time_mins=$(echo "scale=2; ${1}/60" | bc)
        min=$(echo ${time_mins} | cut -d'.' -f1)
        secs="0.$(echo ${time_mins} | cut -d'.' -f2)"
        secs=$(echo ${secs}*60|bc|awk '{print int($1+0.5)}')
    fi
    echo "Time Elapsed : ${min} minutes and ${secs} seconds."
}

start=$(date +%s)

files=(/usr/local/apsis/slowhome/rept/chunks/works_*)
for file in "${files[@]}"; do
    echo "$file"
    itstart=$(date +%s)
    solr/bin/post -c oa_full "$file"
    secs_to_human "$(($(date +%s) - ${itstart}))"
    secs_to_human "$(($(date +%s) - ${start}))"
done
