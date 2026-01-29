
copy the example alembic init and adjust `sqlalchemy.url`
from project root, run
PYTHONPATH=openalex-ingest nacsos_migrate revision --autogenerate --ini-file alembic.secret.ini --message "revision"
PYTHONPATH=openalex-ingest nacsos_migrate upgrade --revision head --ini-file alembic.secret.ini