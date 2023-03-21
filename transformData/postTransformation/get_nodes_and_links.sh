while getopts i:o: flag
do
    case "${flag}" in
        i) id=${OPTARG};;
        o) output=${OPTARG};;
    esac
done
psql -d dev -f network_nodes_and_links.sql -v oa_id=$id -A -t -q -o $output