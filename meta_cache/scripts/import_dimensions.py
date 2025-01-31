import logging
from datetime import datetime
from pathlib import Path
from typing import Generator

import typer
import numpy as np
import pandas as pd
from tqdm import tqdm
from sqlmodel import select, or_
from meta_cache.handlers.schema import Record
from meta_cache.handlers.util import get_ors
from meta_cache.scripts.config import db_engine_cache

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logger = logging.getLogger('copy')


def read_dimensions(directory: Path) -> Generator[Record, None, None]:
    files = list(directory.glob('*.json.gz'))
    logger.info(f'Found {len(files)} globs')
    for file in files:
        df = pd.read_json(file, orient='records', lines=True)

        for _, row in df.iterrows():
            yield Record(
                dimensions_id=row['id'],
                doi=row['doi'],
                pubmed_id=str(int(row['pmid'])) if not pd.isnull(row['pmid']) else None,
                title=row['title'],
                abstract=row['abstract'],
                requested_dimensions=True,
                time_dimensions=datetime.now(),
                raw_dimensions=row.replace({np.nan: None}).to_dict(),
            )


def main(directory: Path = Path('data/')):
    with db_engine_cache.session() as session:
        for reference in tqdm(read_dimensions(directory=directory)):
            existed = False
            for record in session.exec(select(Record).where(or_(*get_ors(reference)))):
                record.sqlmodel_update(reference.model_dump(exclude_unset=True, exclude_none=True))
                session.add(record)
                existed = True
            if not existed:
                session.add(reference)
            session.commit()


if __name__ == "__main__":
    typer.run(main)
