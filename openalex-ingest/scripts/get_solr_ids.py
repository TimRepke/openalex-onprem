import logging
from pathlib import Path
from typing import Annotated

import httpx
import typer
import csv

query = """
(
  (climat* OR "global warming" OR "greenhouse effect" OR "greenhouse effects" OR "greenhouse gas" OR "greenhouse gases" OR "greenhouse gas emissions" OR "greenhouse emissions" OR "GHG emissions" OR "GHGE" OR temperature* OR precipitat* OR rainfall OR "heat index" OR "heat indices" OR "extreme heat event" OR "extreme heat events" OR "heat-wave" OR heatwave OR "extreme-cold*" OR "cold index" OR "cold indices" OR humidity OR drought* OR hydroclim* OR monsoon OR "el nino" OR ENSO OR "sea surface temperature" OR "sea surface temperatures" OR SST OR snowmelt* OR flood* OR storm* OR cyclone* OR hurricane* OR typhoon* OR "sea-level" OR "sea level" OR wildfire* OR "wild-fire" OR "forest-fire" OR "forest fire" OR "forest fires")
  OR
  ({!surround v="(disaster) 3N (risk OR management OR manage OR managing OR natural)"})
  OR
  (({!surround v="extreme 3N event"}) NOT paleo)
  OR

    ({!surround v="(hydrochloroflourocarbons OR pm2.5 OR ammonia OR VOCs OR nox OR hydrochloroflourocarbon OR HFCs OR SO4 OR carbon OR n20 OR halogen OR chlorocarbon OR pm25 OR nh3 OR SOX OR O3 OR ccl4 OR NMVOC OR SO2 OR HFC OR CO OR nitrous OR methane OR ch4 OR co2 OR sulphur OR VOC OR ozone OR chlorocarbons) 3N (emissions OR emitter OR emitting OR mitigate OR emission OR mitigation)"})
)
AND
(
  (health OR wellbeing OR "well-being" OR ill OR illness OR disease* OR syndrome* OR infect* OR medical* OR mortality OR DALY OR morbidity OR injur* OR death* OR hospital* OR acciden* OR emergency OR emergent OR doctor OR GP OR obes* OR overweight OR "over-weight" OR underweight OR "under-weight" OR hunger OR stunting OR wasting OR undernourish* OR undernutrition OR anthropometr* OR malnutrition OR malnour* OR anemia OR anaemia OR "micro-nutrient*" OR hypertension OR "blood pressure" OR stroke OR renovascular OR cardiovascular OR cerebrovascular OR (CVD NOT (vapor OR vapour)) OR "heart disease" OR Isch*emic OR cardio*vascular OR "heart attack" OR "heart attacks" OR coronary OR CHD OR diabet* OR CKD OR renal OR cancer OR kidney OR lithogenes* OR skin OR fever* OR renal* OR rash* OR eczema* OR "thermal stress" OR hypertherm* OR hypotherm* OR pre*term OR stillbirth OR birth*weight OR LBW OR maternal OR pregnan* OR gestation* OR "pre-eclampsia" OR "preeclampsia" OR sepsis OR oligohydramnios OR placenta* OR haemorrhage OR hemorrhage OR malaria OR dengue* OR mosquito* OR chikungunya OR leishmaniasis OR encephalit* OR vector-borne OR pathogen OR zoonos* OR zika* OR "west nile" OR onchocerciasis OR filiariasis OR waterborne OR diarrhoeal OR diarrheal OR gastro* OR (enteric NOT (fermentation OR "enteric CH4" OR "enteric methane")) OR "vibrio bacteria" OR cyanobacteria OR parasit* OR borrelia OR paraly* OR neurotoxi* OR viral OR rotavirus OR noravirus OR hantavirus OR cholera OR protozoa* OR lyme OR tick*borne OR salmonella OR giardia OR shigella OR campylobacter OR food*borne OR aflatoxin OR poison* OR ciguatera OR respiratory OR allerg* OR lung* OR asthma* OR bronchi* OR pulmonary* OR COPD OR rhinitis OR wheez* OR mental OR depress* OR anxi* OR PTSD OR psycho* OR "post*trauma*" OR "pre-trauma*" OR "pretrauma*" OR suicide*
  ) OR 
  ({!surround v="(heat) 3N (stress OR fatigue OR burn OR burns OR stroke OR exhaustion OR cramp)"} NOT cattle
  )
)
"""

BATCH_SIZE = 500

logger = logging.getLogger('copy')


def main(
    solr_host: Annotated[str, typer.Option(prompt='host')],
    solr_collection: Annotated[str, typer.Option(prompt='solr collection')],
    ids_file: Annotated[Path, typer.Option(prompt='path to file where to write IDs')],
    loglevel: str = 'DEBUG',
):
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s (%(process)d): %(message)s', level=loglevel)

    params = {
        'q': query,  # -abstract:[* TO ""]
        'df': 'title_abstract',
        'fl': 'id,doi,external_abstract,abstract',
        # *,locations:[json],authorships:[json],biblio:[json],indexed_in:[json]
        'q.op': 'AND',
        'rows': BATCH_SIZE,
        'sort': 'id desc',
        'cursorMark': '*',
        'defType': 'lucene',
        'useParams': '',
    }

    with httpx.Client() as client, open(ids_file, 'w', newline='') as f_out:
        writer = csv.writer(f_out, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['openalex_id', 'doi', 'has_abstract', 'added_abstract'])
        bi = 1
        num_docs_cum = 0
        while True:
            logger.info(f'----------- Processing batch {bi} -----------')
            bi += 1

            res = client.post(f'{solr_host}/api/collections/{solr_collection}/select', data=params, timeout=60).json()

            next_curser = res.get('nextCursorMark')
            params['cursorMark'] = next_curser
            n_docs_total = res['response']['numFound']
            batch_docs = res['response']['docs']
            n_docs_batch = len(batch_docs)
            num_docs_cum += n_docs_batch

            if n_docs_total > 0:
                logger.debug(f'Current progress: {num_docs_cum:,}/{n_docs_total:,}={num_docs_cum / n_docs_total:.2%} docs')

            if len(batch_docs) == 0:
                logger.info('No documents in this batch, assuming to be done!')
                break

            logger.debug('Appending IDs...')
            for doc in batch_docs:
                writer.writerow(
                    [
                        doc['id'],
                        doc.get('doi', ''),
                        1 if doc.get('abstract') else 0,
                        1 if doc.get('external_abstract') else 0,
                    ]
                )

            if next_curser is None:
                logger.info('Did not receive a `nextCursorMark`, assuming to be done!')
                break


if __name__ == '__main__':
    typer.run(main)
