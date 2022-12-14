#!/bin/bash

process_file() {

    ROOTPATH=$1
    FILE=$2

    PROVIDER=$(basename -- "${FILE%.*.*}")
    echo "unpack $PROVIDER"

    TMP_DIR="$ROOTPATH/core_tmp/$PROVIDER"
    TMP_FULLTEXT="$TMP_DIR/fulltext/"

    DEST_DIR="$ROOTPATH/output/"
    DEST_FULLTEXT="$DEST_DIR/fulltext/"
    DEST_DOCS="$DEST_DIR/docs/provider=$PROVIDER"

    mkdir -p $TMP_FULLTEXT
    mkdir -p $DEST_FULLTEXT
    mkdir -p $DEST_DOCS

    echo $FILE
    tar xf $FILE -C $TMP_DIR

    echo "parse json"

    for JSONFILE in $TMP_DIR/*/*/*.json;
    do
        # Add provider ID field and remove fullText to create and save compacted json.
        jq --argjson provider "$(jo provider_id="$PROVIDER")" '. += $provider' < $JSONFILE |
        jq -c 'del(.fullText)' >> "$DEST_DOCS/documents_$PROVIDER.jsonl"

        # Create separate json with core_id and fullText for relevant ids.
        jq 'with_entries(select(.key | in({"coreId":1,"fullText":1})))' $JSONFILE |
        jq -c 'select(.fullText != null)' >> "$TMP_FULLTEXT/fulltext_$PROVIDER.jsonl"
    done

    tar -c -z -f "$DEST_FULLTEXT/fulltext_$PROVIDER.gz" -C $TMP_FULLTEXT .
    rm -r $TMP_DIR
    rm $FILE
    echo "$PROVIDER finish"
}

ROOTPATH=/var/data/core/output/

SOURCE_DIR="$ROOTPATH/core_output/"
DEST_DIR="$ROOTPATH/output/"
DEST_FULLTEXT="$DEST_DIR/fulltext/"

max_num_processes=500
limited_factor=1
num_processes=$((max_num_processes/limited_factor))

for FILE in `ls -1 $SOURCE_DIR*.tar.xz`;
do
  ((i=i%num_processes)); ((i++==0)) && wait
  process_file "$ROOTPATH" "$FILE" &
done
wait

#tar czf "$DEST_DIR/core_fulltext.gz" -C $DEST_FULLTEXT .
#rm -r $DEST_FULLTEXT
