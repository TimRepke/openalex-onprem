import time
import logging
import argparse
from pathlib import Path

from msgspec import Struct
from msgspec.json import Decoder, Encoder

from invert_index import invert


class InvertedAbstract(Struct):
    IndexLength: int
    InvertedIndex: dict[str, list[int]]


class WorkIds(Struct, omit_defaults=True):
    # doi: str | None = None # redundant with Work.doi
    mag: int | None = None
    # openalex: str
    pmid: str | None = None
    pmcid: str | None = None


class Biblio(Struct, omit_defaults=True):
    volume: str | None = None
    issue: str | None = None
    first_page: str | None = None
    last_page: str | None = None


class DehydratedInstitution(Struct, kw_only=True, omit_defaults=True):
    country_code: str | None = None
    display_name: str | None = None
    id: str | None = None
    ror: str | None = None
    type: str | None = None


class DehydratedAuthor(Struct, omit_defaults=True):
    display_name: str | None = None
    id: str | None = None
    orcid: str | None = None


class Authorship(Struct):
    author: DehydratedAuthor
    author_position: str
    institutions: list[DehydratedInstitution]
    is_corresponding: bool
    raw_affiliation_string: str


class DehydratedSource(Struct, omit_defaults=True, kw_only=True):
    display_name: str
    host_organization: str | None = None
    # host_organization_lineage
    host_organization_name: str | None = None
    id: str
    # is_in_doaj
    # is_oa
    issn: list[str] | None = None
    issn_l: str | None = None
    type: str


class Location(Struct, omit_defaults=True, kw_only=True):
    is_oa: bool
    landing_page_url: str | None = None
    license: str | None = None
    source: DehydratedSource | None = None
    pdf_url: str | None = None
    version: str | None = None


class Work(Struct, kw_only=True, omit_defaults=True):
    abstract_inverted_index: str | None = None
    authorships: list[Authorship]
    # apc_list
    # apc_paid
    # best_oa_location
    biblio: Biblio
    # cited_by_api_url
    cited_by_count: int
    # concepts
    # corresponding_author_ids
    # corresponding_institution_ids
    # counts_by_year
    created_date: str
    display_name: str | None = None
    doi: str | None = None

    # grants
    id: str
    ids: WorkIds
    is_oa: bool | None = None
    is_paratext: bool
    is_retracted: bool
    language: str | None = None
    # license:str
    locations: list[Location]
    # locations_count
    # mesh
    # ngrams_url
    # open_access
    # primary_location
    publication_date: str | None = None
    publication_year: int | None = None
    # referenced_works
    # related_works
    title: str | None = None
    type: str
    # type_crossref
    updated_date: str | None = None
    # ngram
    # ngram_count
    # ngram_tokens
    # term_frequency


class WorkOut(Struct, kw_only=True, omit_defaults=True):
    id: str
    display_name: str | None = None
    title: str | None = None
    abstract: str | None = None
    title_abstract: str | None = None

    authorships: str | None = None  # list[Authorship]
    biblio: str | None = None  # Biblio
    cited_by_count: int
    created_date: str
    doi: str | None = None
    mag: int | None = None
    pmid: str | None = None
    pmcid: str | None = None

    is_oa: bool
    is_paratext: bool
    is_retracted: bool
    language: str | None = None

    locations: str | None = None  # list[Location]

    publication_date: str | None = None
    publication_year: int | None = None
    type: str
    updated_date: str | None = None


def transform_partition(in_file: str|Path, out_file: str|Path) -> tuple[int, int]:
    decoder_work = Decoder(Work)
    decoder_ia = Decoder(InvertedAbstract)
    encoder = Encoder()

    abstracts: int = 0
    works: int = 0
    buffer = bytearray(256)

    with open(in_file, 'rb') as f_in, open(out_file, 'wb') as f_out:
        for line in f_in:
            works += 1
            work = decoder_work.decode(line)
            abstract = None
            if work.abstract_inverted_index is not None:
                ia = decoder_ia.decode(work.abstract_inverted_index)

                abstracts += 1
                inverted_abstract = ia.InvertedIndex

                abstract = invert(inverted_abstract, ia.IndexLength)

            ta = None
            if abstract is not None and work.title is not None:
                ta = work.title + ' ' + abstract

            authorships = None
            if work.authorships is not None and len(work.authorships) > 0:
                authorships = encoder.encode(work.authorships).decode()

            locations = None
            if work.locations is not None and len(work.locations) > 0:
                locations = encoder.encode(work.locations).decode()

            biblio = None
            if work.biblio is not None:
                biblio = encoder.encode(work.biblio).decode()

            mag = None
            pmid = None
            pmcid = None
            if work.ids is not None:
                mag = work.ids.mag
                pmid = work.ids.pmid
                pmcid = work.ids.pmcid

            wo = WorkOut(id=work.id,
                         display_name=work.display_name,
                         title=work.title,
                         abstract=abstract,
                         title_abstract=ta,
                         authorships=authorships,
                         biblio=biblio,
                         cited_by_count=work.cited_by_count,
                         created_date=work.created_date,
                         doi=work.doi,
                         mag=mag,
                         pmid=pmid,
                         pmcid=pmcid,
                         is_oa=work.is_oa,
                         is_paratext=work.is_paratext,
                         is_retracted=work.is_retracted,
                         language=work.language,
                         locations=locations,
                         publication_date=work.publication_date,
                         publication_year=work.publication_year,
                         type=work.type,
                         updated_date=work.updated_date)

            encoder.encode_into(wo, buffer)
            buffer.extend(b'\n')
            f_out.write(buffer)

    return works, abstracts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='PartitionTransformer',
                                     description='Transform OpenAlex partition into our solr format')

    parser.add_argument('infile')
    parser.add_argument('outfile')
    parser.add_argument('-q', '--quiet', action='store_false', dest='log')

    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s (%(process)d): %(message)s',
                        level=logging.INFO if args.log else logging.FATAL)

    startTime = time.time()
    logging.info(f'Processing partition file "{args.infile}" and writing to "{args.outfile}"')

    n_works, n_abstracts = transform_partition(args.infile, args.outfile)

    executionTime = (time.time() - startTime)
    logging.info(f'Found {n_abstracts:,} abstracts in {n_works:,} works in {executionTime}s')

