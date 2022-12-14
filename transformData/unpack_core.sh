#!/bin/bash

ROOTPATH=/var/data/core/output/

SOURCEDIR=$ROOTPATH"core_output/"
TMPDIR=$ROOTPATH"core_tmp/"
DESTDIR=$ROOTPATH"output/"

DESTFULLTEXT=$DESTDIR"fulltext/"
DESTDOCS=$DESTDIR"docs/"

mkdir -p $DESTDIR
mkdir -p $DESTFULLTEXT
mkdir -p $DESTDOCS

for FILE in `ls -1 $SOURCEDIR*.tar.xz`;
do
        PROVIDER=$(basename -- "${FILE%.*.*}")
        echo "$PROVIDER start"
        mkdir -p $TMPDIR
        tar xf $FILE -C $TMPDIR

        # Temp Full Text location
        TMPFULLTEXT=$TMPDIR"/fulltext"

        # Locations for final output
        DOCS=$DESTDOCS"provider="$PROVIDER

        mkdir -p $DOCS
        mkdir -p $TMPFULLTEXT

        for JSONFILE in $TMPDIR*/*/*.json;
        do
          # Add provider ID field and remove fullText to create and save compacted json.
          jq --argjson provider "$(jo provider_id="$PROVIDER")" '. += $provider' < $JSONFILE |
          jq -c 'del(.fullText)' >> $DOCS/documents_"$PROVIDER".jsonl

          # Create separate json with core_id and fullText for relevant ids.
          jq 'with_entries(select(.key | in({"coreId":1,"fullText":1})))' $JSONFILE |
          jq -c 'select(.fullText != null)' >> $TMPFULLTEXT/fulltext_"$PROVIDER".jsonl
        done

        tar czf $DESTFULLTEXT/fulltext_"$PROVIDER".gz -C $TMPFULLTEXT .
        rm -r $TMPDIR
        rm $FILE
    echo "$PROVIDER finish"
done

tar czf $DESTDIR/core_fulltext.gz -C $DESTFULLTEXT .
rm -r $DESTFULLTEXT
