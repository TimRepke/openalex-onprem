from pathlib import Path

from shared.util import get_ids_to_delete, batched, ObjectType

table_map: dict[ObjectType, list[tuple[str, str]]] = {
    # NOTE: We are only deleting based on the "primary" table.
    #       We assume, that any other references (e.g. authorships) are updated on
    #       the other end (e.g. via works) if an author is removed.
    'author': [
        ('authors', 'id')
    ],
    'institution': [
        ('institutions', 'id'),
        ('institutions_association', 'institution_a_id'),
        ('institutions_concept', 'institution_id')
    ],
    'publisher': [
        ('publishers', 'id')
    ],
    'source': [
        ('sources', 'id')
    ],
    'concept': [
        ('concepts', 'id'),
        ('concepts_ancestor', 'concept_a_id'),
        ('concepts_related', 'concept_a_id')
    ],
    'funder': [
        ('funders', 'id')
    ],
    'work': [
        ('works', 'id'),
        ('works_authorships', 'work_id'),
        ('works_concepts', 'work_id'),
        ('works_locations', 'work_id'),
        ('works_references', 'work_a_id'),  # we are not explicitly deleting the other direction (`work_b_id`)
        ('works_related', 'work_a_id')
    ]
}


def filter_none(lst):
    return [l for l in lst if l is not None]


def generate_deletions(ids: list[str],
                       object_type: ObjectType,
                       pg_schema: str,
                       batch_size: int = 1000):
    for del_batch in batched(ids, batch_size):
        id_lst = "','".join(filter_none(del_batch))
        for table, key in table_map[object_type]:
            yield f"DELETE FROM {pg_schema}.{table} t WHERE t.{key} IN ('{id_lst}');"


def generate_deletions_from_merge_file(merge_files: list[Path],
                                       out_file: Path,
                                       object_type: ObjectType,
                                       pg_schema: str,
                                       batch_size: int = 1000):
    out_file.parent.mkdir(exist_ok=True, parents=True)
    with open(out_file, 'w') as f:
        for del_batch in batched(get_ids_to_delete(merge_files), batch_size):
            id_lst = "','".join(filter_none(del_batch))
            for table, key in table_map[object_type]:
                f.write(f"DELETE FROM {pg_schema}.{table} t WHERE t.{key} IN ('{id_lst}');\n")
