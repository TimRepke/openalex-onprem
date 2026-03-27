import typer

from .match.sync import main as retain_old

app = typer.Typer()

app.command('retain-old', help='Process old snapshot and write abstracts that are now missing to meta-cache and solr')(retain_old)

__all__ = [
    'app',
]