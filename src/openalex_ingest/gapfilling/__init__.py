import typer

from .queue_ids import main as queue_ids
from .random_sample import main as random_sample

app = typer.Typer()

app.command('sample-ids', help='Generate a random sample of IDs from the solr index')(random_sample)
app.command('queue-ids', help="Given a file with IDs you'd like gap-filled, this puts it in the queue")(queue_ids)
