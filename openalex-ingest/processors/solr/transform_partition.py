import time
import gzip
import logging
import argparse
from pathlib import Path

from msgspec.json import Decoder, Encoder

from processors.solr import structs
from shared.cyth.invert_index import invert


def transform_partition(in_file: str | Path, out_file: str | Path) -> tuple[int, int]:
    decoder_work = Decoder(structs.Work)
    decoder_ia = Decoder(structs.InvertedAbstract)
    encoder = Encoder()

    abstracts: int = 0
    works: int = 0
    buffer = bytearray(256)

    with gzip.open(in_file, 'rb') as f_in, open(out_file, 'wb') as f_out:
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

            wo = structs.WorkOut(id=work.id,
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
