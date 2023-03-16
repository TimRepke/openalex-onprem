import asyncio
import json
import uuid
import logging

from psycopg.errors import UniqueViolation
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from nacsos_data.db import get_engine_async
from nacsos_data.db.schemas import m2m_import_item_table, Import
from nacsos_data.db.schemas.items.academic import AcademicItem
from nacsos_data.models.imports import M2MImportItemType, ImportType
from nacsos_data.models.items.academic import AcademicItemModel

from nacsos_data.util.academic.duplicate import find_duplicates


async def upload():
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s: %(message)s', level=logging.DEBUG)
    logger = logging.getLogger('nacsos-upload')
    logger.setLevel(logging.WARN)

    ENV_FILE = 'scripts/.env'  # db connection info
    SOURCE_FILE = 'data/niklas.jsonl'
    USER_ID = '088011c5-546b-4c4a-b099-54ab59a7a99a'  # niklas
    PROJECT_ID = '02243368-9f48-4813-9f16-b8ce8bbab1ca'  # carbon pricing map
    # pick one of those (use existing import or create new one)
    IMPORT_NAME = 'Initial OA import'
    IMPORT_UUID: uuid.UUID | str | None = 'b89ec3ea-f6ea-4a8f-9039-85e6dcc08a2a'

    db_engine = get_engine_async(conf_file=ENV_FILE)

    async with db_engine.session() as session:  # type: AsyncSession
        with open(SOURCE_FILE, 'r') as f_in:
            if IMPORT_UUID is not None:
                logger.info('Using existing import')
                imp = (await session.scalars(select(Import).where(Import.import_id == IMPORT_UUID))).one_or_none()
                if imp is None:
                    raise RuntimeError('no import')
            elif IMPORT_NAME is not None:
                logger.info('Creating new import')
                IMPORT_UUID = uuid.uuid4()
                imp = Import(project_id=PROJECT_ID,
                             user_id=USER_ID,
                             import_id=IMPORT_UUID,
                             name=IMPORT_NAME,
                             description='',
                             type=ImportType.script)
                session.add(imp)
                await session.commit()
            else:
                raise ValueError()

            for line in f_in:
                doc_ = json.loads(line)
                doi: str | None = doc_.get('doi')
                if doi is not None:
                    doi = doi.replace('https://doi.org/', '')
                doc = AcademicItemModel(project_id=PROJECT_ID,
                                        openalex_id=doc_.get('id'),
                                        doi=doi,
                                        title=doc_.get('title'),
                                        text=doc_.get('abstract'),
                                        publication_year=doc_.get('publication_year'),
                                        meta={
                                            'cited_by_count': doc_.get('cited_by_count'),
                                            'publication_date': doc_.get('publication_date'),
                                            'type': doc_.get('type')
                                        })
                logger.debug(doc)
                logger.info(f'Importing AcademicItem with doi {doc.doi} and title "{doc.title}"')

                duplicates = await find_duplicates(item=doc,
                                                   project_id=PROJECT_ID,
                                                   check_oa_id=True,
                                                   check_doi=True,
                                                   session=session)
                try:
                    if not duplicates:
                        logger.debug(' -> Creating new!')
                        item_id = str(uuid.uuid4())
                        doc.item_id = item_id
                        session.add(AcademicItem(**doc.dict()))
                        await session.commit()
                    else:
                        item_id = duplicates[0]
                        logger.debug(f' -> Has {len(duplicates)} duplicates; using {item_id}.')

                    if IMPORT_UUID is not None:
                        stmt_m2m = insert(m2m_import_item_table) \
                            .values(item_id=item_id, import_id=IMPORT_UUID, type=M2MImportItemType.explicit)
                        try:
                            await session.execute(stmt_m2m)
                            await session.commit()
                            logger.debug(' -> Added many-to-many relationship for import/item')
                        except IntegrityError:
                            logger.debug(f' -> M2M_i2i already exists, ignoring {IMPORT_UUID} <-> {item_id}')
                            await session.rollback()
                except (UniqueViolation, IntegrityError) as e:
                    logger.exception(e)
                    await session.rollback()


if __name__ == '__main__':
    asyncio.run(upload())
