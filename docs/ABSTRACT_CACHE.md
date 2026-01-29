# Abstract cache workflow

You have an ID (DOI, WoS ID, Scopus ID, OpenAlex ID, Dimensions ID, PubMed ID, SemanticScholar ID) and would like to get
additional meta-data from various sources for those.
Ideally, you post your request as a tuple of as many cross-platform IDs as you can. In this way, we later know that a
specific DOI and OpenAlex and Scopus ID belong to the same record. The information flow after posting the request is as follows:

* Entry is added in the Queue table
* Every database has workers that routinely check the queue for new entries
* Every database worker decides when it might work on the request (collecting many requests is a good idea for databases that bill by request, not by number of records)
* The request has options, for example which databases to query with what priority (`sources`) and how to handle the case where something related is already in the cache (`on_conflict`)
* When a worker picks up a job from the queue, it does not update the entry yet. After it made its request to the database, it will write responses to the `requests` table and update the `queue` accordingly.
   * Remove itself from the `sources` list and update the record
   * Based on `on_conflict` and the other source priorities, update the remaining list
   * If the source list is empty, delete the record from the `queue`