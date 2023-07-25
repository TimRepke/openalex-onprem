from msgspec.json import Decoder
from msgspec import Struct
# from test import invert
import test
import time

startTime = time.time()


class Work(Struct):
    abstract_inverted_index: str | None


decoder_work = Decoder(Work)

abstracts = 0
works = 0
with open('../../data/part_001', 'r') as f:
    for line in f:
        works += 1

        data = decoder_work.decode(line)
        if data.abstract_inverted_index is None:
            continue

        abstract = test.invert(data.abstract_inverted_index)
        abstracts += 1

executionTime = (time.time() - startTime)
print(f'Found {abstracts:,} abstracts in {works:,} works')
print('Execution time in seconds: ' + str(executionTime))
# Found 32,055 abstracts in 46,890 works
# Execution time in seconds: 2.1709041595458984
