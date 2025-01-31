import json

from processors.solr_daily.structs import Work, WorkOut, LocationOut
from shared.util import strip_id


def revert_index(inverted_index: dict[str, list[int]] | None) -> str | None:
    if inverted_index is None:
        return None

    token: str
    position: int
    positions: list[int]

    abstract_length: int = len([1 for idxs in inverted_index.values() for _ in idxs])
    abstract: list[str] = [''] * abstract_length

    for token, positions in inverted_index.items():
        for position in positions:
            if position < abstract_length:
                abstract[position] = token

    return ' '.join(abstract)


def transform_work(work: Work) -> WorkOut:
    wid = strip_id(work.id)

    abstract = None
    if work.abstract_inverted_index is not None:
        try:
            abstract = revert_index(work.abstract_inverted_index)
            if len(abstract.strip()) == 0:
                abstract = None
        except:
            abstract = None

    ta = None
    if abstract is not None or work.title is not None:
        ta = (work.title if work.title is not None else '') + ' ' + (abstract if abstract is not None else '')

    locations = None
    if work.locations is not None and len(work.locations) > 0:
        locations = json.dumps([
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
            ).model_dump(exclude_unset=True, exclude_none=True)
            for loc in work.locations])

    authorships = None
    if work.authorships is not None and len(work.authorships) > 0:
        authorships = json.dumps([a.model_dump(exclude_unset=True, exclude_none=True) for a in work.authorships])

    publisher = None
    publisher_id = None
    if work.primary_location is not None and work.primary_location.source is not None:
        publisher_id = work.primary_location.source.host_organization
        publisher = work.primary_location.source.host_organization_name

    topics = None
    if work.topics is not None and len(work.topics) > 0:
        topics = json.dumps([t.model_dump(exclude_unset=True, exclude_none=True) for t in work.topics])

    indexed_in = None
    if work.indexed_in is not None and len(work.indexed_in) > 0:
        indexed_in = json.dumps(work.indexed_in)

    biblio = None
    if work.biblio is not None and work.biblio.volume is not None:
        biblio = work.biblio.model_dump_json(exclude_unset=True, exclude_none=True)

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

    return WorkOut(id=wid,
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
                 #topics=topics,
                 type=work.type,
                 created_date=work.created_date,
                 updated_date=work.updated_date)
