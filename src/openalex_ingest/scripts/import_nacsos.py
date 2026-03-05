raise DeprecationWarning('Outdated, not migrated yet.')

# import logging
# from datetime import datetime
# from typing import Generator
#
# import typer
# from sqlmodel import select, or_
# import sqlalchemy as sa
#
# from meta_cache.handlers.schema import Record
# from meta_cache.handlers.util import get_ors
# from meta_cache.scripts.config import db_engine_nacsos, db_engine_cache
#
# logger = logging.getLogger('copy')
#
#
# def nacsos_items(project_id: str, batch_size: int = 100) -> Generator[Record, None, None]:
#     stmt = sa.text("""
#        SELECT i.text as abstract, ai.title,
#              ai.doi, ai.wos_id, ai.scopus_id, ai.openalex_id, ai.s2_id, ai.pubmed_id, ai.dimensions_id,
#              ai.meta as raw_other
#        FROM item i
#        LEFT JOIN academic_item ai ON ai.item_id = i.item_id
#        WHERE i.project_id = :pid
#               AND
#                   i.text IS NOT NULL
#               AND
#            (     ai.dimensions_id IS NOT NULL
#               OR ai.openalex_id IS NOT NULL
#               OR ai.doi IS NOT NULL
#               OR ai.pubmed_id IS NOT NULL
#               OR ai.scopus_id IS NOT NULL
#               OR ai.s2_id IS NOT NULL
#               OR ai.wos_id IS NOT NULL
#               OR ai.scopus_id IS NOT NULL)
#        """)
#     with db_engine_nacsos.engine.connect() as connection:
#         with connection.execution_options(yield_per=batch_size).execute(stmt, {'pid': project_id}) as result:
#             for pi, partition in enumerate(result.partitions(batch_size)):
#                 logger.debug(f'Received partition {pi} ({len(partition)}) from nacsos.')
#                 yield from [
#                     Record(
#                         **dict(row),
#                         requested_other=True,
#                         time_other=datetime.now(),
#                     )
#                     for row in partition
#                 ]
#
#
# def main(project_id: str, batch_size: int = 100):
#     with db_engine_cache.session() as session:
#         for reference in nacsos_items(project_id, batch_size):
#             existed = False
#             for record in session.exec(select(Record).where(or_(*get_ors(reference)))):
#                 record.sqlmodel_update(reference.model_dump(exclude_unset=True, exclude_none=True))
#                 session.add(record)
#                 existed = True
#             if not existed:
#                 session.add(reference)
#             session.commit()
#
#
# if __name__ == '__main__':
#     typer.run(main)
