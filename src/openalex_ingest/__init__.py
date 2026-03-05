import typer
from openalex_ingest.daily.fix_abstracts import app as daily_fix_app
from openalex_ingest.daily.pull_api_update import app as pull_api_update_app
from openalex_ingest.worker.main import main as queue_worker


def main():
    app = typer.Typer(name='openalex', help='Toolkit for keeping a local OpenAlex snapshot up-to-date and filled with abstracts')
    app.add_typer(daily_fix_app, name='fix')
    app.add_typer(pull_api_update_app, name='api-pull')
    app.command('queue-worker', help='Work on getting abstracts for queued entries for a set amount of time')(queue_worker)
    app()


if __name__ == '__main__':
    main()
