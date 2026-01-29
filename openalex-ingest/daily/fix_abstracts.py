def request_meta_cache(url: str, meta_key: str, buffer: list[WorkOut], wrapper: str | None = None):
    orig_size = len(buffer)
    buffer = [work for work in buffer if (int(work.id is not None) + int(work.pmid is not None) + int(work.doi is not None)) > 1]
    logging.info(f'Submitting {len(buffer)} of {orig_size} works with missing abstract to meta-cache')
    try:
        res = httpx.post(
            url,
            headers={'x-auth-key': meta_key},
            json={
                'references': [
                    {
                        'openalex_id': work.id,
                        'doi': work.doi[16:] if work.doi else None,
                        'pubmed_id': str(work.pmid) if work.pmid else None,
                    }
                    for work in buffer
                ],
                'limit': len(buffer) * 4,
                'wrapper': wrapper,
                'fetch_on_missing_abstract': True,
                'fetch_on_missing_entry': True,
                'update_links': True,
                'empty_abstract_as_missing': True,
            },
            timeout=120,
        )
        res.raise_for_status()
        info = res.json()
        logging.info(
            f'Hits: {info["n_hits"]}, updates: {info["n_updated"]}, queued: {info["n_queued"]}, missed: {info["n_missed"]}, added: {info["n_added"]}',
        )
    except httpx.HTTPError as e:
        logging.error(f'Failed to submit {url}: {e}')
        logging.warning(e.response.text)
        logging.exception(e)


@app.command()
def request_abstracts(
    conf_file: Annotated[Path, typer.Option(prompt='.env config file')],
    auth_key: Annotated[str, typer.Option(prompt='meta-cache key')],
    created_since: Annotated[str, typer.Option(callback=date_check, help='Get works created on or after')],
    created_until: Annotated[
        str | None,
        typer.Option(
            callback=date_check,
            help='Get works created on or after',
        ),
    ] = None,
    use_updated: bool = True,
    batch_size: int = 200,
    wrapper: str | None = None,
    loglevel: str = 'INFO',
):
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s (%(process)d): %(message)s', level=loglevel)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    conf_file = conf_file.absolute().resolve()
    logging.info(f'Loading settings from {conf_file}')
    settings = Settings(_env_file=str(conf_file), _env_file_encoding='utf-8')  # type: ignore[call-arg]
    db_engine = get_engine(settings=settings)
    logging.debug(f'Using solr at {settings.OA_SOLR}')

    end_date = 'NOW'
    if created_until:
        end_date = f'{end_date}T01:01:00.123Z'
    date_field = 'created_date'
    if use_updated:
        date_field = 'updated_date'

    with httpx.Client() as client:
        cursor = '*'
        page = 1
        t0 = time()
        while True:
            t1 = time()
            res = client.post(
                f'{settings.OA_SOLR}/select',
                data={
                    'q': '-abstract:*',
                    'fq': f'{date_field}:[{created_since}T01:01:00Z TO {end_date}]',
                    'fl': 'id,doi',
                    'q.op': 'AND',
                    'rows': batch_size,
                    'useParams': '',
                    'sort': 'id desc',
                    'defType': 'lucene',
                    'cursorMark': cursor,
                },
                timeout=60,
            ).json()
            page += 1
            cursor = res.get('nextCursorMark')
            n_docs_total = res['response']['numFound']
            batch_docs = res['response']['docs']
            logging.info(f'Got batch with {len(batch_docs):,} records, now at {batch_size * page:,}/{n_docs_total:,}')

            if len(res['response']['docs']) == 0:
                logging.info('No data in batch, assuming done!')
                break

            logging.debug(
                f'Done with page {page} in {timedelta(seconds=time() - t1)}h; {timedelta(seconds=time() - t0)}h passed overall',
            )

            if cursor is None:
                logging.info('Did not receive a `nextCursorMark`, assuming to be done!')
                break

            references = [Reference(openalex_id=doc['id'], doi=doc['doi'][16:]) for doc in res['response']['docs'] if doc.get('doi') is not None]
            if len(references) == 0:
                logging.info('  > Batch has no DOIs.')
                continue

            logging.info(f'  > {len(references)} references with missing abstract have a DOI')

            remaining = references
            for wrapper_cls in get_wrappers(keys=wrapper):
                logging.debug(f'  > Using {wrapper_cls.name} on {len(remaining):,}/{len(references):,} references')
                try:
                    cache_response = wrapper_cls.run(
                        db_engine=db_engine,
                        references=remaining,
                        auth_key=auth_key,
                        skip_existing=True,
                    )
                    remaining = [Reference(openalex_id=ref.openalex_id, doi=ref.doi) for ref in cache_response.references if ref.missed or not ref.abstract]
                except Exception as e:
                    logging.exception(e)
                    logging.warning(f'Ignoring {e} and continuing...')

                if len(remaining) == 0:
                    logging.info('No references remaining')
                    break


@app.command()
def backfill_abstracts(
    solr_host: Annotated[str, typer.Option(help='Solr base url')],
    solr_collection: Annotated[str, typer.Option(help='Name of the Solr collection')],
    conf_file: Annotated[str, typer.Option(help='Path to configuration .env file')],
    created_since: Annotated[
        str,
        typer.Option(
            callback=date_check,
            help='Get works created on or after',
        ),
    ],
    batch_size: int = 200,
    loglevel: str = 'INFO',
):
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s (%(process)d): %(message)s', level=loglevel)

    logging.info(f'Connecting to database.')
    db_engine = get_engine(conf_file=conf_file)

    logging.info(f'Starting backfill of abstracts.')
    update_solr_abstracts(
        db_engine=db_engine,
        solr_host=solr_host,
        solr_collection=solr_collection,
        from_time=datetime.strptime(created_since, '%Y-%m-%d'),
        batch_size=batch_size,
    )
    logging.info(f'Finished backfill of abstracts.')
