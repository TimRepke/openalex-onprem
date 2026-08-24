import typer

from .match.sync import main as retain_old
from .match.sync import keep_from_solr
from .load import update_solr

app = typer.Typer()

app.command('retain-solr', help='Check works in new S3 snapshot against existing solr instance and retain abstracts that are now missing in meta-cache')(
    keep_from_solr
)
app.command('retain-old', help='Process old snapshot and write abstracts that are now missing to meta-cache and solr')(retain_old)
app.command('ingest', help='Ingest S3 snapshot')(update_solr)

__all__ = [
    'app',
]
