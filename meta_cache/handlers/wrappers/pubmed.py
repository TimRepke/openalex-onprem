import logging
from datetime import datetime
from typing import Any, Generator
from xml.etree.ElementTree import Element, fromstring as parse_xml

from meta_cache.handlers.db import DatabaseEngine
from meta_cache.handlers.models import Reference, Request
from meta_cache.handlers.util import RequestClient, batched, xml2dict
from meta_cache.handlers.wrappers.base import AbstractWrapper
from meta_cache.handlers.schema import ApiKey

logger = logging.getLogger('wrapper-pubmed')
PAGE_SIZE = 10


class PubmedWrapper(AbstractWrapper):
    name = 'pubmed'
    db_field_id = 'pubmed_id'

    @staticmethod
    def get_title(article: Element) -> str | None:
        hits = article.findall('.//ArticleTitle')
        if len(hits) > 0:
            return ' '.join(hits[0].itertext())
        return None

    @staticmethod
    def get_abstract(article: Element) -> str | None:
        hits = article.findall('.//Abstract')
        if len(hits) > 0:
            return '\n\n'.join(hits[0].itertext())
        return None

    @staticmethod
    def get_doi(article: Element) -> str | None:
        hits = article.findall('.//ArticleId[@IdType="doi"]')
        if len(hits) > 0:
            return hits[0].text
        return None

    @staticmethod
    def get_id(article: Element) -> str | None:
        hits = article.findall('.//PMID')
        if len(hits) > 0:
            return hits[0].text
        return None

    @staticmethod
    def _api_key_query_extra() -> str:
        return ''

    @classmethod
    def log_api_key_use(cls, db_engine: DatabaseEngine, key: ApiKey) -> None:
        with db_engine.session() as session:
            orm_key = session.get(ApiKey, key.api_key_id)
            if not orm_key:
                logger.warning(f'Failed to log API key use: {key}')
            orm_key.sqlmodel_update({
                'last_used': datetime.now(),
            })
            session.add(orm_key)
            session.commit()

    @classmethod
    def fetch(cls,
              db_engine: DatabaseEngine,
              references: list[Reference],
              auth_key: str) -> Generator[Request, None, None]:
        parts = []
        for reference in references:
            if reference.pubmed_id:
                parts.append(f'{reference.pubmed_id}[PMID]')
            if reference.doi:
                parts.append(f'"{reference.doi}"[DOI]')

        if len(parts) == 0:
            raise ValueError('Found no scopus ids or DOIs to query pubed')

        # direct lookup via
        # https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?api_key=KEY&db=pubmed&id=17975326
        # can be comma separated!
        # DOCS: https://www.ncbi.nlm.nih.gov/books/NBK25497/

        n_records = 0
        with RequestClient(timeout=120, max_req_per_sec=3) as request_client:
            for n_pages, parts_batch in enumerate(batched(parts, batch_size=PAGE_SIZE)):
                key = cls.get_api_keys(db_engine=db_engine, auth_key=auth_key)[0]

                logger.info(f'Fetching search context (page {n_pages})...')
                search_page = request_client.get(
                    'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',
                    params={
                        'api_key': key.api_key,
                        'db': 'pubmed',
                        'term': ' OR '.join(parts_batch),
                        'usehistory': 'y',
                    },
                )
                tree = parse_xml(search_page.text)
                web_env = tree.find('WebEnv').text
                query_key = tree.find('QueryKey').text

                result_page = request_client.get(
                    'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi',
                    params={
                        'api_key': key.api_key,
                        'db': 'pubmed',
                        'WebEnv': web_env,
                        'query_key': query_key,
                    },
                )
                cls.log_api_key_use(db_engine=db_engine, key=key)

                tree = parse_xml(result_page.text)
                for article in tree.findall('PubmedArticle'):
                    entry = xml2dict(article)
                    n_records += 1
                    yield Request(
                        wrapper=cls.name,
                        api_key_id=key.api_key_id,
                        title=cls.get_title(article),
                        abstract=cls.get_abstract(article),
                        doi=cls.get_doi(article),
                        pubmed_id=cls.get_id(article),
                        raw=entry,
                    )
                logger.debug(f'Found {n_records:,} records after processing page {n_pages}')


if __name__ == '__main__':
    from meta_cache.server.db import db_engine as engine
    import os

    for ri, record in enumerate(PubmedWrapper.fetch(
            db_engine=engine,
            references=[
                Reference(pubmed_id='17975327'),
                Reference(doi='10.1046/j.1464-410x.1997.02667.x'),
            ],
            auth_key=os.getenv('AUTH_KEY'))):
        print(record)
        if ri > 100:
            break
    print('Force stopped')
