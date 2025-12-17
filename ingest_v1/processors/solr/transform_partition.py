import time
import gzip
import logging
import argparse
from io import BytesIO
from pathlib import Path

from msgspec import DecodeError
from msgspec.json import Decoder, Encoder

from shared.cyth.invert_index import invert

from processors.solr.structs import LocationOut, Topic
from shared.util import strip_id

from processors.solr import structs


def transform_partition(in_file: str | Path, output: BytesIO) -> tuple[int, int]:
    decoder_work = Decoder(structs.Work)
    encoder = Encoder()

    n_abstracts: int = 0
    n_works: int = 0
    buffer = bytearray(256)

    with gzip.open(in_file, 'rb') as f_in:
        for line in f_in:
            n_works += 1
            try:
                work = decoder_work.decode(line)
            except Exception as e:
                print(line)
                raise e
            wid = strip_id(work.id)

            abstract = None
            if work.abstract_inverted_index is not None:
                try:
                    abstract = invert(work.abstract_inverted_index)
                    if len(abstract.strip()) > 0:
                        n_abstracts += 1
                    else:
                        abstract = None
                except DecodeError:
                    logging.warning(f'Failed to read abstract for {wid} in {in_file}')
                    abstract = None

            ta = None
            if abstract is not None or work.title is not None:
                ta = (work.title if work.title is not None else '') + ' ' + (abstract if abstract is not None else '')

            authorships = None
            if work.authorships is not None and len(work.authorships) > 0:
                authorships = encoder.encode(work.authorships).decode()

            locations = None
            publisher = None
            publisher_id = None
            source = None
            source_id = None
            if work.locations is not None and len(work.locations) > 0:
                locations = encoder.encode([
                    LocationOut(
                        is_oa=loc.is_oa,
                        is_primary=(work.primary_location is not None
                                    and work.primary_location.source is not None
                                    and loc.source is not None
                                    and work.primary_location.source.id == loc.source.id
                                    and work.primary_location.source.display_name == loc.source.display_name
                                    and work.primary_location.pdf_url == loc.pdf_url
                                    and work.primary_location.version == loc.version),
                        landing_page_url=loc.landing_page_url,
                        license=loc.license,
                        source=loc.source,
                        pdf_url=loc.pdf_url,
                        version=loc.version
                    )
                    for loc in work.locations]).decode()
                if work.locations[0].source is not None:
                    publisher_id = work.locations[0].source.host_organization
                    publisher = work.locations[0].source.host_organization_name
                    source = work.locations[0].source.display_name
                    source_id = work.locations[0].source.id

            topics = None
            if work.topics is not None and len(work.topics) > 0:
                topics = encoder.encode(work.topics).decode()

            indexed_in = None
            if work.indexed_in is not None and len(work.indexed_in) > 0:
                indexed_in = encoder.encode(work.indexed_in).decode()

            biblio = None
            if work.biblio is not None and work.biblio.volume is not None:
                biblio = encoder.encode(work.biblio).decode()

            mag = None
            pmid = None
            pmcid = None
            if work.ids is not None:
                mag = str(work.ids.mag)
                pmid = work.ids.pmid
                pmcid = work.ids.pmcid

            is_published = None
            is_accepted = None
            if work.primary_location:
                is_published = work.primary_location.is_published
                is_accepted = work.primary_location.is_accepted

            is_oa = None
            if work.open_access:
                is_oa = work.open_access.is_oa

            references = None
            if work.referenced_works is not None and len(work.referenced_works) > 0:
                references = encoder.encode(work.referenced_works).decode()

            wo = structs.WorkOut(id=wid,
                                 # display_name=work.display_name,
                                 title=work.title,
                                 abstract=abstract,
                                 title_abstract=ta,
                                 authorships=authorships,
                                 biblio=biblio,
                                 cited_by_count=work.cited_by_count,
                                 doi=work.doi,
                                 mag=mag,
                                 pmid=pmid,
                                 pmcid=pmcid,
                                 indexed_in=indexed_in,
                                 is_oa=is_oa,
                                 is_paratext=work.is_paratext,
                                 is_retracted=work.is_retracted,
                                 is_published=is_published,
                                 is_accepted=is_accepted,
                                 language=work.language,
                                 locations=locations,
                                 publication_date=work.publication_date,
                                 publication_year=work.publication_year,
                                 publisher=publisher,
                                 publisher_id=publisher_id,
                                 source=source,
                                 source_id=source_id,
                                 references=references,
                                 topics=topics,
                                 type=work.type,
                                 created_date=work.created_date,
                                 updated_date=work.updated_date)

            encoder.encode_into(wo, buffer)
            buffer.extend(b'\n')
            output.write(buffer)

    return n_works, n_abstracts


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

    _n_works, _n_abstracts = transform_partition(args.infile, args.outfile)

    executionTime = (time.time() - startTime)
    logging.info(f'Found {_n_abstracts:,} abstracts in {_n_works:,} works in {executionTime}s')
