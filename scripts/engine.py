from sqlalchemy import create_engine, text, URL
from sqlalchemy.orm import sessionmaker
from dotenv import dotenv_values

config = dotenv_values()

connection_str = URL.create(
    drivername='postgresql+psycopg',
    username=config['USER'],
    password=config['PASSWORD'],
    host=config['HOST'],
    port=config['PORT'],
    database=config['DATABASE'],
)
engine = create_engine(connection_str, echo=False)
smkr = sessionmaker(bind=engine, autoflush=False, autocommit=False)

__all__ = ['smkr', 'engine']
