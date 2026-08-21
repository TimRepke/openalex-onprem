import random
import logging
from itertools import chain

from nacsos_data.util.academic.apis.scopus import ScopusAPI

loglevel = logging.INFO
logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s (%(process)d): %(message)s', level=loglevel)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('root').setLevel(loglevel)

logger = logging.getLogger('scopus')
api_logger = logger.getChild('api')
api_logger.setLevel(logging.WARNING)

with open('conf/scopus.keys', 'r') as f:
    keys = [
        line.strip()
        for line in f
        if not line.strip().startswith('#')
    ]
    random.shuffle(keys)

logger.info(f'Identified {len(keys):,} keys')

api = ScopusAPI(
    api_key=keys[0],
    # proxy: str | None = None,
    # max_req_per_sec: int = 5,
    # max_retries: int = 5,
    # backoff_rate: float = 5.0,
    # ignored_exceptions: list[Type[Exception]] | None = None,
    # logger: logging.Logger | None = None,
    logger=api_logger,
)

query = f'( LOAD-DATE AFT 20260301 )'
cnt = api.fetch_n_results(query=query)
logger.info(f'{cnt} for "{query}"')

# https://service.elsevier.com/app/answers/detail/a_id/11365/supporthub/scopus/kw/field+code/

logger.info('')
logger.info(api.api_feedback)
logger.info('')

ranges = [
    ('20241231', '20250201'),
    ('20250131', '20250301'),
    ('20250228', '20250401'),
    ('20250331', '20250501'),
    ('20250430', '20250601'),
    ('20250531', '20250701'),
    ('20250630', '20250801'),
    ('20250731', '20250901'),
    ('20250831', '20251001'),
    ('20250930', '20251101'),
    ('20251031', '20251201'),
    ('20251130', '20260101'),
    ('20251231', '20260201'),
    ('20260131', '20260301'),
    ('20260228', '20260401'),
    ('20260331', '20260501'),
    ('20260430', '20260601'),
    ('20260531', '20260701'),
    ('20260630', '20260801'),
    ('20260731', '20260901'),
    ('20260831', '20261001'),
]
for begin, end in ranges:
    query = f'(LOAD-DATE AFT {begin}) AND ( LOAD-DATE BEF {end} )'
    cnt = api.fetch_n_results(query=query)
    logger.info(f'{cnt} for "{query}"')

logger.info('')
logger.info(api.api_feedback)
logger.info('')

for sti in 'abcdefghijklmnopqrstuvxyz':
    for stj in 'abcdefghijklmnopqrstuvxyz':
        query = f'FIRSTAUTH ( {sti}{stj}* ) AND ( LOAD-DATE AFT 20260301 )'
        cnt = api.fetch_n_results(query=query)
        logger.info(f'{cnt} for "{query}"')

logger.info('')
logger.info(api.api_feedback)
logger.info('')

for sti in 'abcdefghijklmnopqrstuvxyz':
    for stj in 'abcdefghijklmnopqrstuvxyz':
        query = f'TITLE ( {sti}{stj}* ) AND ( LOAD-DATE AFT 20260301 )'
        cnt = api.fetch_n_results(query=query)
        logger.info(f'{cnt} for "{query}"')

logger.info('')
logger.info(api.api_feedback)
logger.info('')

for sti in 'abcdefghijklmnopqrstuvxyz':
    for stj in 'abcdefghijklmnopqrstuvxyz':
        query = f'SRCTITLE ( {sti}{stj}* ) AND ( LOAD-DATE AFT 20260301 )'
        cnt = api.fetch_n_results(query=query)
        logger.info(f'{cnt} for "{query}"')

logger.info('')
logger.info(api.api_feedback)
logger.info('')

for dt in chain(
    range(20260501, 20260532),
    range(20260601, 20260618),
):
    query = f'SRCTITLE ( pa* ) AND ( LOAD-DATE AFT {dt} )'
    cnt = api.fetch_n_results(query=query)
    logger.info(f'{cnt} for "{query}"')

logger.info(api.api_feedback)

# 2026-06-23 19:40:28,351 [INFO] scopus (257682): 998044 for "(LOAD-DATE AFT 20241231) AND ( LOAD-DATE BEF 20250201 )"
# 2026-06-23 19:40:29,373 [INFO] scopus (257682): 796958 for "(LOAD-DATE AFT 20250131) AND ( LOAD-DATE BEF 20250301 )"
# 2026-06-23 19:40:30,516 [INFO] scopus (257682): 3677579 for "(LOAD-DATE AFT 20250228) AND ( LOAD-DATE BEF 20250401 )"
# 2026-06-23 19:40:31,625 [INFO] scopus (257682): 884812 for "(LOAD-DATE AFT 20250331) AND ( LOAD-DATE BEF 20250501 )"
# 2026-06-23 19:40:32,789 [INFO] scopus (257682): 3038161 for "(LOAD-DATE AFT 20250430) AND ( LOAD-DATE BEF 20250601 )"
# 2026-06-23 19:40:34,084 [INFO] scopus (257682): 1962632 for "(LOAD-DATE AFT 20250531) AND ( LOAD-DATE BEF 20250701 )"
# 2026-06-23 19:40:35,316 [INFO] scopus (257682): 585977 for "(LOAD-DATE AFT 20250630) AND ( LOAD-DATE BEF 20250801 )"
# 2026-06-23 19:40:36,543 [INFO] scopus (257682): 990529 for "(LOAD-DATE AFT 20250731) AND ( LOAD-DATE BEF 20250901 )"
# 2026-06-23 19:40:37,767 [INFO] scopus (257682): 4384908 for "(LOAD-DATE AFT 20250831) AND ( LOAD-DATE BEF 20251001 )"
# 2026-06-23 19:40:38,807 [INFO] scopus (257682): 3887818 for "(LOAD-DATE AFT 20250930) AND ( LOAD-DATE BEF 20251101 )"
# 2026-06-23 19:40:39,716 [INFO] scopus (257682): 2033667 for "(LOAD-DATE AFT 20251031) AND ( LOAD-DATE BEF 20251201 )"
# 2026-06-23 19:40:41,160 [INFO] scopus (257682): 2422012 for "(LOAD-DATE AFT 20251130) AND ( LOAD-DATE BEF 20260101 )"
# 2026-06-23 19:40:42,380 [INFO] scopus (257682): 2333003 for "(LOAD-DATE AFT 20251231) AND ( LOAD-DATE BEF 20260201 )"
# 2026-06-23 19:40:43,361 [INFO] scopus (257682): 4316360 for "(LOAD-DATE AFT 20260131) AND ( LOAD-DATE BEF 20260301 )"
# 2026-06-23 19:40:44,837 [INFO] scopus (257682): 4496219 for "(LOAD-DATE AFT 20260228) AND ( LOAD-DATE BEF 20260401 )"
# 2026-06-23 19:40:46,334 [INFO] scopus (257682): 3902164 for "(LOAD-DATE AFT 20260331) AND ( LOAD-DATE BEF 20260501 )"
# 2026-06-23 19:40:47,398 [INFO] scopus (257682): 8774485 for "(LOAD-DATE AFT 20260430) AND ( LOAD-DATE BEF 20260601 )"
# 2026-06-23 19:40:48,831 [INFO] scopus (257682): 3102625 for "(LOAD-DATE AFT 20260531) AND ( LOAD-DATE BEF 20260701 )"
#
#
#
# 2026-06-17 18:32:33,185 [INFO] scopus (107587): 280209 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260501 )"
# 2026-06-17 18:32:34,085 [INFO] scopus (107587): 279534 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260502 )"
# 2026-06-17 18:32:35,195 [INFO] scopus (107587): 278959 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260503 )"
# 2026-06-17 18:32:36,471 [INFO] scopus (107587): 278546 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260504 )"
# 2026-06-17 18:32:37,342 [INFO] scopus (107587): 271735 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260505 )"
# 2026-06-17 18:32:38,304 [INFO] scopus (107587): 265005 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260506 )"
# 2026-06-17 18:32:39,419 [INFO] scopus (107587): 257980 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260507 )"
# 2026-06-17 18:32:40,405 [INFO] scopus (107587): 257604 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260508 )"
# 2026-06-17 18:32:41,357 [INFO] scopus (107587): 215920 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260509 )"
# 2026-06-17 18:32:42,205 [INFO] scopus (107587): 192183 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260510 )"
# 2026-06-17 18:32:43,314 [INFO] scopus (107587): 190878 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260511 )"
# 2026-06-17 18:32:44,280 [INFO] scopus (107587): 188060 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260512 )"
# 2026-06-17 18:32:45,261 [INFO] scopus (107587): 179796 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260513 )"
# 2026-06-17 18:32:46,300 [INFO] scopus (107587): 173690 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260514 )"
# 2026-06-17 18:32:47,188 [INFO] scopus (107587): 167057 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260515 )"
# 2026-06-17 18:32:48,189 [INFO] scopus (107587): 165600 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260516 )"
# 2026-06-17 18:32:49,121 [INFO] scopus (107587): 164849 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260517 )"
# 2026-06-17 18:32:50,042 [INFO] scopus (107587): 164432 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260518 )"
# 2026-06-17 18:32:51,213 [INFO] scopus (107587): 156750 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260519 )"
# 2026-06-17 18:32:52,270 [INFO] scopus (107587): 154166 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260520 )"
# 2026-06-17 18:32:53,362 [INFO] scopus (107587): 151216 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260521 )"
# 2026-06-17 18:32:54,513 [INFO] scopus (107587): 148750 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260522 )"
# 2026-06-17 18:32:55,607 [INFO] scopus (107587): 147200 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260523 )"
# 2026-06-17 18:32:56,838 [INFO] scopus (107587): 147077 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260524 )"
# 2026-06-17 18:32:57,816 [INFO] scopus (107587): 141243 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260525 )"
# 2026-06-17 18:32:58,787 [INFO] scopus (107587): 101024 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260526 )"
# 2026-06-17 18:32:59,791 [INFO] scopus (107587): 95168 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260527 )"
# 2026-06-17 18:33:00,772 [INFO] scopus (107587): 68192 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260528 )"
# 2026-06-17 18:33:01,866 [INFO] scopus (107587): 63977 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260529 )"
# 2026-06-17 18:33:02,899 [INFO] scopus (107587): 60562 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260530 )"
# 2026-06-17 18:33:04,162 [INFO] scopus (107587): 56145 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260531 )"
#
# 2026-06-17 18:33:05,144 [INFO] scopus (107587): 50121 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260532 )"
# 2026-06-17 18:33:06,104 [INFO] scopus (107587): 46591 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260533 )"
# 2026-06-17 18:33:07,041 [INFO] scopus (107587): 36903 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260534 )"
# 2026-06-17 18:33:16,280 [INFO] scopus (107587): 34897 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260535 )"
# 2026-06-17 18:33:17,506 [INFO] scopus (107587): 31490 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260536 )"
# 2026-06-17 18:33:19,446 [INFO] scopus (107587): 26699 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260537 )"
# 2026-06-17 18:33:21,877 [INFO] scopus (107587): 24943 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260538 )"
#
# 2026-06-17 18:36:28,090 [INFO] scopus (108100): 50121 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260601 )"
# 2026-06-17 18:36:29,207 [INFO] scopus (108100): 46591 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260602 )"
# 2026-06-17 18:36:30,296 [INFO] scopus (108100): 36903 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260603 )"
# 2026-06-17 18:36:31,192 [INFO] scopus (108100): 34897 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260604 )"
# 2026-06-17 18:36:32,366 [INFO] scopus (108100): 31490 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260605 )"
# 2026-06-17 18:36:33,645 [INFO] scopus (108100): 26699 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260606 )"
# 2026-06-17 18:36:34,626 [INFO] scopus (108100): 24943 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260607 )"
# 2026-06-17 18:36:35,630 [INFO] scopus (108100): 23166 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260608 )"
# 2026-06-17 18:36:36,716 [INFO] scopus (108100): 22538 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260609 )"
# 2026-06-17 18:36:37,727 [INFO] scopus (108100): 21449 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260610 )"
# 2026-06-17 18:36:38,781 [INFO] scopus (108100): 15226 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260611 )"
# 2026-06-17 18:36:39,953 [INFO] scopus (108100): 10561 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260612 )"
# 2026-06-17 18:36:41,111 [INFO] scopus (108100): 8797 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260613 )"
# 2026-06-17 18:36:42,068 [INFO] scopus (108100): 7161 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260614 )"
# 2026-06-17 18:36:42,402 [INFO] scopus (108100): 0 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260615 )"
# 2026-06-17 18:36:42,808 [INFO] scopus (108100): 0 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260616 )"
# 2026-06-17 18:36:43,221 [INFO] scopus (108100): 0 for "SRCTITLE ( pa* ) AND ( LOAD-DATE AFT 20260617 )"
# 2026-06-17 18:36:43,221 [INFO] scopus (108100): {'scopus_requests_limit': '20000', 'scopus_requests_remaining': '19217', 'scopus_requests_reset': '1782108386'}
