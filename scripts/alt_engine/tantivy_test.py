from pathlib import Path
import time
import tantivy
import csv

# Declaring our schema.
schema_builder = tantivy.SchemaBuilder()
schema_builder.add_text_field("oaid", stored=True)
schema_builder.add_text_field("doi", stored=True)
schema_builder.add_unsigned_field("py", stored=True)
schema_builder.add_text_field("title", stored=True)
schema_builder.add_text_field("abstract", stored=True)
schema_builder.add_unsigned_field("citations", stored=True)
schema = schema_builder.build()

INDEX_FILE = '/home/tim/workspace/nacsos-academic-search/data/tantivy'
LOAD = True

if LOAD:
    print(f'creating index at {INDEX_FILE}')
    index = tantivy.Index(schema, path=INDEX_FILE, reuse=False)
    t0 = time.time()
    writer = index.writer()
    with open('/home/tim/workspace/nacsos-academic-search/data/works_sample.csv') as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        t1 = time.time()
        for i, row in enumerate(csvreader):
            writer.add_document(tantivy.Document(
                oaid=row['id'],
                doi=row['doi'],
                py=row['publication_year'],
                title=row['title'],
                abstract=row['abstract'],
                citations=row['cited_by_count']
            ))

            if (i % 100000) == 0 and i > 0:
                print(f'added documents in {time.time() - t1}s')
                print(f'committing @ {i}')
                t1 = time.time()
                writer.commit()
                print(f'committing took {time.time() - t1}s; total time passed {time.time() - t0}')
                t1 = time.time()

    print('final commit')
    t1 = time.time()
    writer.commit()
    print(f'committing took {time.time() - t1}s; total time passed {time.time() - t0}')
else:
    index = tantivy.Index.open(INDEX_FILE)

index.reload()
searcher = index.searcher()
query = index.parse_query("fish days", ["title", "body"])
(best_score, best_doc_address) = searcher.search(query, 3).hits[0]
best_doc = searcher.doc(best_doc_address)
print(best_doc)

