from pathlib import Path

from shared.util import get_ids_to_delete, batched, ObjectType
from shared.config import settings

table_map: dict[ObjectType, list[str]] = {
    'author': [
        # ('authors', 'id'),
        # ('authors_counts_by_year', 'author_id'),
        # ('authors_ids', 'author_id'),
        # TODO
    ],
    'institution': [
        # TODO
    ],
    'publisher': [
        # TODO
    ],
    'source': [
        # TODO
    ],
    'work': [
        # TODO
    ]
}


def filter_none(lst):
    return [l for l in lst if l is not None]


def generate_deletions(ids: list[str],
                       object_type: ObjectType,
                       batch_size: int = 1000):
    for del_batch in batched(ids, batch_size):
        id_lst = "','".join(filter_none(del_batch))
        for table, key in table_map[object_type]:
            yield f"DELETE FROM {settings.pg_schema}.{table} t WHERE t.{key} IN ('{id_lst}');"


def generate_deletions_from_merge_file(merge_files: list[Path],
                                       out_file: Path,
                                       object_type: ObjectType,
                                       batch_size: int = 1000):
    out_file.parent.mkdir(exist_ok=True, parents=True)
    with open(out_file, 'w') as f:
        for del_batch in batched(get_ids_to_delete(merge_files), batch_size):
            id_lst = "','".join(filter_none(del_batch))
            for table, key in table_map[object_type]:
                f.write(f"DELETE FROM {settings.pg_schema}.{table} t WHERE t.{key} IN ('{id_lst}');\n")
