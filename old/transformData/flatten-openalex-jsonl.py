import csv
import glob
import gzip
import json
import os

SNAPSHOT_DIR = '/var/data/openalex'
CSV_DIR = '/var/data/openalex/csv-files'

FILES_PER_ENTITY = int(os.environ.get('OPENALEX_DEMO_FILES_PER_ENTITY', '0'))

csv_files = {
    'institutions': {
        'institutions': {
            'name': os.path.join(CSV_DIR, 'institutions.csv.gz'),
            'columns': [
                'id', 'ror', 'display_name', 'type', 'country_code', 'homepage_url', 'image_url', 'image_thumbnail_url',
                'display_name_acroynyms', 'display_name_alternatives', 'works_count', 'cited_by_count',
                'updated_date'
            ]
        },
        'ids': {
            'name': os.path.join(CSV_DIR, 'institutions_ids.csv.gz'),
            'columns': [
                'institution_id', 'openalex', 'ror', 'grid', 'wikipedia', 'wikidata', 'mag'
            ]
        },
        'geo': {
            'name': os.path.join(CSV_DIR, 'institutions_geo.csv.gz'),
            'columns': [
                'institution_id', 'city', 'geonames_city_id', 'region', 'country_code', 'country', 'latitude',
                'longitude'
            ]
        },
        'associated_institutions': {
            'name': os.path.join(CSV_DIR, 'institutions_associated_institutions.csv.gz'),
            'columns': [
                'institution_id', 'associated_institution_id', 'relationship'
            ]
        },
        'counts_by_year': {
            'name': os.path.join(CSV_DIR, 'institutions_counts_by_year.csv.gz'),
            'columns': [
                'institution_id', 'year', 'works_count', 'cited_by_count'
            ]
        }
    },
    'authors': {
        'authors': {
            'name': os.path.join(CSV_DIR, 'authors.csv.gz'),
            'columns': [
                'id', 'orcid', 'display_name', 'display_name_alternatives', 'works_count', 'cited_by_count',
                'last_known_institution', 'updated_date'
            ]
        },
        'ids': {
            'name': os.path.join(CSV_DIR, 'authors_ids.csv.gz'),
            'columns': [
                'author_id', 'openalex', 'orcid', 'scopus', 'twitter', 'wikipedia', 'mag'
            ]
        },
        'counts_by_year': {
            'name': os.path.join(CSV_DIR, 'authors_counts_by_year.csv.gz'),
            'columns': [
                'author_id', 'year', 'works_count', 'cited_by_count'
            ]
        }
    },
    'concepts': {
        'concepts': {
            'name': os.path.join(CSV_DIR, 'concepts.csv.gz'),
            'columns': [
                'id', 'wikidata', 'display_name', 'level', 'description', 'works_count', 'cited_by_count', 'updated_date'
            ]
        },
        'ancestors': {
            'name': os.path.join(CSV_DIR, 'concepts_ancestors.csv.gz'),
            'columns': ['concept_id', 'ancestor_id']
        },
        'counts_by_year': {
            'name': os.path.join(CSV_DIR, 'concepts_counts_by_year.csv.gz'),
            'columns': ['concept_id', 'year', 'works_count', 'cited_by_count']
        },
        'ids': {
            'name': os.path.join(CSV_DIR, 'concepts_ids.csv.gz'),
            'columns': ['concept_id', 'openalex', 'wikidata', 'wikipedia', 'umls_aui', 'umls_cui', 'mag']
        },
        'related_concepts': {
            'name': os.path.join(CSV_DIR, 'concepts_related_concepts.csv.gz'),
            'columns': ['concept_id', 'related_concept_id', 'score']
        }
    },
    'venues': {
        'venues': {
            'name': os.path.join(CSV_DIR, 'venues.csv.gz'),
            'columns': [
                'id', 'issn_l', 'issn', 'display_name', 'publisher', 'works_count', 'cited_by_count', 'is_oa',
                'is_in_doaj', 'homepage_url', 'updated_date'
            ]
        },
        'ids': {
            'name': os.path.join(CSV_DIR, 'venues_ids.csv.gz'),
            'columns': ['venue_id', 'openalex', 'issn_l', 'issn', 'mag']
        },
        'counts_by_year': {
            'name': os.path.join(CSV_DIR, 'venues_counts_by_year.csv.gz'),
            'columns': ['venue_id', 'year', 'works_count', 'cited_by_count']
        },
    },
    'works': {
        'works': {
            'name': os.path.join(CSV_DIR, 'works.csv.gz'),
            'columns': [
                'id', 'doi', 'mag', 'pmid', 'pmcid', 'title', 'publication_year', 'publication_date', 'type', 'cited_by_count',
                'is_retracted', 'is_paratext', 'is_open_access', 'abstract'
            ]
        },
        'host_venues': {
            'name': os.path.join(CSV_DIR, 'works_host_venues.csv.gz'),
            'columns': [
                'work_id', 'venue_id', 'url', 'is_oa', 'version', 'license'
            ]
        },
        'alternate_host_venues': {
            'name': os.path.join(CSV_DIR, 'works_alternate_host_venues.csv.gz'),
            'columns': [
                'work_id', 'venue_id', 'url', 'is_oa', 'version', 'license'
            ]
        },
        'authorships': {
            'name': os.path.join(CSV_DIR, 'works_authorships.csv.gz'),
            'columns': [
                'work_id', 'author_position', 'author_id', 'institution_id', 'raw_affiliation_string'
            ]
        },
        'biblio': {
            'name': os.path.join(CSV_DIR, 'works_biblio.csv.gz'),
            'columns': [
                'work_id', 'volume', 'issue', 'first_page', 'last_page'
            ]
        },
        'concepts': {
            'name': os.path.join(CSV_DIR, 'works_concepts.csv.gz'),
            'columns': [
                'work_id', 'concept_id', 'score'
            ]
        },
        'mesh': {
            'name': os.path.join(CSV_DIR, 'works_mesh.csv.gz'),
            'columns': [
                'work_id', 'descriptor_ui', 'descriptor_name', 'qualifier_ui', 'qualifier_name', 'is_major_topic'
            ]
        },
        'referenced_works': {
            'name': os.path.join(CSV_DIR, 'works_referenced_works.csv.gz'),
            'columns': [
                'work_id', 'referenced_work_id'
            ]
        },
        'open_access': {
            'name': os.path.join(CSV_DIR, 'works_open_access.csv.gz'),
            'columns': [
                'work_id', 'oa_status', 'oa_url'
            ]
        }
    },
}


def strip_id(src):
    if isinstance(src, dict) and src.get('id'):
        src_id = src.get('id')
    else:
        src_id = src

    return src_id.removeprefix("https://openalex.org/")


def build_abstract(src):

    word_index = []

    for k, v in eval(src).items():
        if k == chr(34):
            k = k+k
        for index in v:
            word_index.append([k, index])

    word_index = sorted(word_index, key=lambda x: x[1])
    abstract = ' '.join([val[0] for val in word_index]).encode('utf-8', 'replace')

    return abstract


def flatten_concepts():
    with gzip.open(csv_files['concepts']['concepts']['name'], 'wt', encoding='utf-8') as concepts_csv, \
            gzip.open(csv_files['concepts']['ancestors']['name'], 'wt', encoding='utf-8') as ancestors_csv, \
            gzip.open(csv_files['concepts']['counts_by_year']['name'], 'wt', encoding='utf-8') as counts_by_year_csv, \
            gzip.open(csv_files['concepts']['ids']['name'], 'wt', encoding='utf-8') as ids_csv, \
            gzip.open(csv_files['concepts']['related_concepts']['name'], 'wt', encoding='utf-8') as related_concepts_csv:

        concepts_writer = csv.DictWriter(
            concepts_csv, fieldnames=csv_files['concepts']['concepts']['columns'], extrasaction='ignore'
        )
        concepts_writer.writeheader()

        ancestors_writer = csv.DictWriter(ancestors_csv, fieldnames=csv_files['concepts']['ancestors']['columns'])
        ancestors_writer.writeheader()

        counts_by_year_writer = csv.DictWriter(counts_by_year_csv, fieldnames=csv_files['concepts']['counts_by_year']['columns'])
        counts_by_year_writer.writeheader()

        ids_writer = csv.DictWriter(ids_csv, fieldnames=csv_files['concepts']['ids']['columns'])
        ids_writer.writeheader()

        related_concepts_writer = csv.DictWriter(related_concepts_csv, fieldnames=csv_files['concepts']['related_concepts']['columns'])
        related_concepts_writer.writeheader()

        seen_concept_ids = set()

        files_done = 0
        for jsonl_file_name in glob.glob(os.path.join(SNAPSHOT_DIR, 'data', 'concepts', '*', '*.gz')):
            print(jsonl_file_name)
            with gzip.open(jsonl_file_name, 'r') as concepts_jsonl:
                for concept_json in concepts_jsonl:
                    if not concept_json.strip():
                        continue

                    concept = json.loads(concept_json)
                    concept["id"] = strip_id(concept)

                    if not (concept_id := concept.get('id')) or concept_id in seen_concept_ids:
                        continue

                    seen_concept_ids.add(concept_id)

                    concepts_writer.writerow(concept)

                    if concept_ids := concept.get('ids'):
                        concept_ids['concept_id'] = concept_id
                        concept_ids['umls_aui'] = json.dumps(concept_ids.get('umls_aui'))
                        concept_ids['umls_cui'] = json.dumps(concept_ids.get('umls_cui'))
                        ids_writer.writerow(concept_ids)

                    if ancestors := concept.get('ancestors'):
                        for ancestor in ancestors:
                            if ancestor.get('id'):
                                ancestor_id = strip_id(ancestor)
                                ancestors_writer.writerow({
                                    'concept_id': concept_id,
                                    'ancestor_id': ancestor_id
                                })

                    if counts_by_year := concept.get('counts_by_year'):
                        for count_by_year in counts_by_year:
                            count_by_year['concept_id'] = concept_id
                            counts_by_year_writer.writerow(count_by_year)

                    if related_concepts := concept.get('related_concepts'):
                        for related_concept in related_concepts:
                            if related_concept.get('id'):
                                related_concept_id = strip_id(related_concept)
                                related_concepts_writer.writerow({
                                    'concept_id': concept_id,
                                    'related_concept_id': related_concept_id,
                                    'score': related_concept.get('score')
                                })

            files_done += 1
            if FILES_PER_ENTITY and files_done >= FILES_PER_ENTITY:
                break


def flatten_venues():
    with gzip.open(csv_files['venues']['venues']['name'], 'wt', encoding='utf-8') as venues_csv, \
            gzip.open(csv_files['venues']['ids']['name'], 'wt', encoding='utf-8') as ids_csv, \
            gzip.open(csv_files['venues']['counts_by_year']['name'], 'wt', encoding='utf-8') as counts_by_year_csv:

        venues_writer = csv.DictWriter(
            venues_csv, fieldnames=csv_files['venues']['venues']['columns'], extrasaction='ignore'
        )
        venues_writer.writeheader()

        ids_writer = csv.DictWriter(ids_csv, fieldnames=csv_files['venues']['ids']['columns'])
        ids_writer.writeheader()

        counts_by_year_writer = csv.DictWriter(counts_by_year_csv, fieldnames=csv_files['venues']['counts_by_year']['columns'])
        counts_by_year_writer.writeheader()

        seen_venue_ids = set()

        files_done = 0
        for jsonl_file_name in glob.glob(os.path.join(SNAPSHOT_DIR, 'data', 'venues', '*', '*.gz')):
            print(jsonl_file_name)
            with gzip.open(jsonl_file_name, 'r') as venues_jsonl:
                for venue_json in venues_jsonl:
                    if not venue_json.strip():
                        continue

                    venue = json.loads(venue_json)
                    venue["id"] = strip_id(venue)

                    if not (venue_id := venue.get('id')) or venue_id in seen_venue_ids:
                        continue

                    seen_venue_ids.add(venue_id)

                    venue['issn'] = json.dumps(venue.get('issn'))
                    venues_writer.writerow(venue)

                    if venue_ids := venue.get('ids'):
                        venue_ids['issn'] = json.dumps(venue_ids.get('issn'))
                        ids_writer.writerow({
                            'venue_id': venue_id,
                            'openalex': venue_ids.get("openalex"),
                            'issn_l': venue_ids.get("issn_l"),
                            'issn': venue_ids.get("issn"),
                            'mag': venue_ids.get("mag")
                        })

                    if counts_by_year := venue.get('counts_by_year'):
                        for count_by_year in counts_by_year:
                            count_by_year['venue_id'] = venue_id
                            counts_by_year_writer.writerow(count_by_year)

            files_done += 1
            if FILES_PER_ENTITY and files_done >= FILES_PER_ENTITY:
                break


def flatten_institutions():
    file_spec = csv_files['institutions']

    with gzip.open(file_spec['institutions']['name'], 'wt', encoding='utf-8') as institutions_csv, \
            gzip.open(file_spec['ids']['name'], 'wt', encoding='utf-8') as ids_csv, \
            gzip.open(file_spec['geo']['name'], 'wt', encoding='utf-8') as geo_csv, \
            gzip.open(file_spec['associated_institutions']['name'], 'wt', encoding='utf-8') as associated_institutions_csv, \
            gzip.open(file_spec['counts_by_year']['name'], 'wt', encoding='utf-8') as counts_by_year_csv:

        institutions_writer = csv.DictWriter(
            institutions_csv, fieldnames=file_spec['institutions']['columns'], extrasaction='ignore'
        )
        institutions_writer.writeheader()

        ids_writer = csv.DictWriter(ids_csv, fieldnames=file_spec['ids']['columns'])
        ids_writer.writeheader()

        geo_writer = csv.DictWriter(geo_csv, fieldnames=file_spec['geo']['columns'])
        geo_writer.writeheader()

        associated_institutions_writer = csv.DictWriter(
            associated_institutions_csv, fieldnames=file_spec['associated_institutions']['columns']
        )
        associated_institutions_writer.writeheader()

        counts_by_year_writer = csv.DictWriter(counts_by_year_csv, fieldnames=file_spec['counts_by_year']['columns'])
        counts_by_year_writer.writeheader()

        seen_institution_ids = set()

        files_done = 0
        for jsonl_file_name in glob.glob(os.path.join(SNAPSHOT_DIR, 'data', 'institutions', '*', '*.gz')):
            print(jsonl_file_name)
            with gzip.open(jsonl_file_name, 'r') as institutions_jsonl:
                for institution_json in institutions_jsonl:
                    if not institution_json.strip():
                        continue

                    institution = json.loads(institution_json)
                    institution["id"] = strip_id(institution)

                    if not (institution_id := institution.get('id')) or institution_id in seen_institution_ids:
                        continue

                    seen_institution_ids.add(institution_id)

                    # institutions
                    institution['display_name_acroynyms'] = json.dumps(institution.get('display_name_acroynyms'))
                    institution['display_name_alternatives'] = json.dumps(institution.get('display_name_alternatives'))
                    institutions_writer.writerow(institution)

                    # ids
                    if institution_ids := institution.get('ids'):
                        institution_ids['institution_id'] = institution_id
                        ids_writer.writerow(institution_ids)

                    # geo
                    if institution_geo := institution.get('geo'):
                        institution_geo['institution_id'] = institution_id
                        geo_writer.writerow(institution_geo)

                    # associated_institutions
                    if associated_institutions := institution.get(
                        'associated_institutions', institution.get('associated_insitutions')  # typo in api
                    ):
                        for associated_institution in associated_institutions:
                            if associated_institution.get('id'):
                                associated_institution_id = strip_id(associated_institution)
                                associated_institutions_writer.writerow({
                                    'institution_id': institution_id,
                                    'associated_institution_id': associated_institution_id,
                                    'relationship': associated_institution.get('relationship')
                                })

                    # counts_by_year
                    if counts_by_year := institution.get('counts_by_year'):
                        for count_by_year in counts_by_year:
                            count_by_year['institution_id'] = institution_id
                            counts_by_year_writer.writerow(count_by_year)

            files_done += 1
            if FILES_PER_ENTITY and files_done >= FILES_PER_ENTITY:
                break


def flatten_authors():
    file_spec = csv_files['authors']

    with gzip.open(file_spec['authors']['name'], 'wt', encoding='utf-8') as authors_csv, \
            gzip.open(file_spec['ids']['name'], 'wt', encoding='utf-8') as ids_csv, \
            gzip.open(file_spec['counts_by_year']['name'], 'wt', encoding='utf-8') as counts_by_year_csv:

        authors_writer = csv.DictWriter(
            authors_csv, fieldnames=file_spec['authors']['columns'], extrasaction='ignore'
        )
        authors_writer.writeheader()

        ids_writer = csv.DictWriter(ids_csv, fieldnames=file_spec['ids']['columns'])
        ids_writer.writeheader()

        counts_by_year_writer = csv.DictWriter(counts_by_year_csv, fieldnames=file_spec['counts_by_year']['columns'])
        counts_by_year_writer.writeheader()

        files_done = 0
        for jsonl_file_name in glob.glob(os.path.join(SNAPSHOT_DIR, 'data', 'authors', '*', '*.gz')):
            print(jsonl_file_name)
            with gzip.open(jsonl_file_name, 'r') as authors_jsonl:
                for author_json in authors_jsonl:
                    if not author_json.strip():
                        continue

                    author = json.loads(author_json)
                    author["id"] = strip_id(author)

                    if not (author_id := author.get('id')):
                        continue

                    # authors
                    author['display_name_alternatives'] = json.dumps(author.get('display_name_alternatives'))
                    author['last_known_institution'] = (author.get('last_known_institution') or {}).get('id')
                    authors_writer.writerow(author)

                    # ids
                    if author_ids := author.get('ids'):
                        author_ids['author_id'] = author_id
                        ids_writer.writerow(author_ids)

                    # counts_by_year
                    if counts_by_year := author.get('counts_by_year'):
                        for count_by_year in counts_by_year:
                            count_by_year['author_id'] = author_id
                            counts_by_year_writer.writerow(count_by_year)
            files_done += 1
            if FILES_PER_ENTITY and files_done >= FILES_PER_ENTITY:
                break



def flatten_works():
    file_spec = csv_files['works']

    with gzip.open(file_spec['works']['name'], 'wt', encoding='utf-8') as works_csv, \
            gzip.open(file_spec['host_venues']['name'], 'wt', encoding='utf-8') as host_venues_csv, \
            gzip.open(file_spec['alternate_host_venues']['name'], 'wt', encoding='utf-8') as alternate_host_venues_csv, \
            gzip.open(file_spec['authorships']['name'], 'wt', encoding='utf-8') as authorships_csv, \
            gzip.open(file_spec['biblio']['name'], 'wt', encoding='utf-8') as biblio_csv, \
            gzip.open(file_spec['concepts']['name'], 'wt', encoding='utf-8') as concepts_csv, \
            gzip.open(file_spec['mesh']['name'], 'wt', encoding='utf-8') as mesh_csv, \
            gzip.open(file_spec['referenced_works']['name'], 'wt', encoding='utf-8') as referenced_works_csv, \
            gzip.open(file_spec['open_access']['name'], 'wt', encoding='utf-8') as open_access_csv:

        works_writer = init_dict_writer(works_csv, file_spec['works'], extrasaction='ignore')
        host_venues_writer = init_dict_writer(host_venues_csv, file_spec['host_venues'])
        alternate_host_venues_writer = init_dict_writer(alternate_host_venues_csv, file_spec['alternate_host_venues'])
        authorships_writer = init_dict_writer(authorships_csv, file_spec['authorships'])
        biblio_writer = init_dict_writer(biblio_csv, file_spec['biblio'])
        concepts_writer = init_dict_writer(concepts_csv, file_spec['concepts'])
        mesh_writer = init_dict_writer(mesh_csv, file_spec['mesh'])
        referenced_works_writer = init_dict_writer(referenced_works_csv, file_spec['referenced_works'])
        open_access_writer = init_dict_writer(open_access_csv, file_spec['open_access'])

        files_done = 0
        for jsonl_file_name in glob.glob(os.path.join(SNAPSHOT_DIR, 'data', 'works', '*', '*.gz')):
            print(jsonl_file_name)
            with gzip.open(jsonl_file_name, 'r') as works_jsonl:
                for work_json in works_jsonl:
                    if not work_json.strip():
                        continue

                    work = json.loads(work_json)
                    work["id"] = strip_id(work)

                    if not (work_id := work.get('id')):
                        continue

                    # works
                    if (abstract := work.get('abstract_inverted_index')) is not None:
                        work['abstract'] = build_abstract(json.dumps(abstract))

                    work["mag"] = work.get('ids').get('mag')
                    work["pmid"] = work.get('ids').get('pmid')
                    work["pmcid"] = work.get('ids').get('pmcid')
                    work["is_open_access"] = work.get('open_access').get('is_oa')

                    works_writer.writerow(work)

                    # host_venues
                    if host_venue := (work.get('primary_location') or work.get('host_venue') or {}):
                        if host_venue.get('id'):
                            host_venue_id = strip_id(host_venue)
                            host_venues_writer.writerow({
                                'work_id': work_id,
                                'venue_id': host_venue_id,
                                'url': host_venue.get('url'),
                                'is_oa': host_venue.get('is_oa'),
                                'version': host_venue.get('version'),
                                'license': host_venue.get('license'),
                            })

                    if open_access := work.get('open_access'):
                        open_access_writer.writerow({
                            'work_id': work_id,
                            'oa_status': open_access.get('oa_status'),
                            'oa_url': open_access.get('oa_url'),
                        })

                    # alternate_host_venues
                    if alternate_host_venues := work.get('alternate_host_venues'):
                        for alternate_host_venue in alternate_host_venues:
                            if alternate_host_venue.get('id'):
                                venue_id = strip_id(alternate_host_venue)
                                alternate_host_venues_writer.writerow({
                                    'work_id': work_id,
                                    'venue_id': venue_id,
                                    'url': alternate_host_venue.get('url'),
                                    'is_oa': alternate_host_venue.get('is_oa'),
                                    'version': alternate_host_venue.get('version'),
                                    'license': alternate_host_venue.get('license'),
                                })

                    # authorships
                    if authorships := work.get('authorships'):
                        for authorship in authorships:
                            if author_id := authorship.get('author', {}).get('id'):
                                author_id = strip_id(author_id)
                                institutions = authorship.get('institutions')
                                institution_ids = [i.get('id') for i in institutions]
                                institution_ids = [strip_id(i) for i in institution_ids if i]
                                institution_ids = institution_ids or [None]

                                for institution_id in institution_ids:
                                    authorships_writer.writerow({
                                        'work_id': work_id,
                                        'author_position': authorship.get('author_position'),
                                        'author_id': author_id,
                                        'institution_id': institution_id,
                                        'raw_affiliation_string': authorship.get('raw_affiliation_string'),
                                    })

                    # biblio
                    if biblio := work.get('biblio'):
                        biblio['work_id'] = work_id
                        biblio_writer.writerow(biblio)

                    # concepts
                    for concept in work.get('concepts'):
                        if concept.get('id'):
                            concept_id = strip_id(concept)
                            concepts_writer.writerow({
                                'work_id': work_id,
                                'concept_id': concept_id,
                                'score': concept.get('score'),
                            })

                    # mesh
                    for mesh in work.get('mesh'):
                        mesh['work_id'] = work_id
                        mesh_writer.writerow(mesh)

                    # referenced_works
                    for referenced_work in work.get('referenced_works'):
                        if referenced_work:
                            referenced_works_writer.writerow({
                                'work_id': work_id,
                                'referenced_work_id': strip_id(referenced_work)
                            })

            files_done += 1
            if FILES_PER_ENTITY and files_done >= FILES_PER_ENTITY:
                break


def init_dict_writer(csv_file, file_spec, **kwargs):
    writer = csv.DictWriter(
        csv_file, fieldnames=file_spec['columns'], **kwargs
    )
    writer.writeheader()
    return writer


if __name__ == '__main__':
    if not os.path.isdir(CSV_DIR):
        os.mkdir(CSV_DIR)

    flatten_concepts()
    flatten_venues()
    flatten_institutions()
    flatten_authors()
    flatten_works()
