from sqlalchemy import create_engine, text, URL
from sqlalchemy.orm import sessionmaker

connection_str = URL.create(
    drivername='postgresql+psycopg',
    username='tim',
    password='YZLkCS*XcDS3^yErs!&pGu7dY5GT@s',
    host='178.63.8.118',
    port=5432,
    database='dev',
)
engine = create_engine(connection_str, echo=False)
smkr = sessionmaker(bind=engine, autoflush=False, autocommit=False)

__all__ = ['smkr']
