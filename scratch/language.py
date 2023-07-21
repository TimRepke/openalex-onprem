import re
from collections import Counter
import fasttext
from engine import smkr
from sqlalchemy import text

model = fasttext.load_model('lid.176.bin')

BATCH = 100000
MAX = 10000000
stats = []
rg = re.compile(r'\n')
with smkr() as session:
    for b in range(0, MAX, BATCH):
        stmt = text('SELECT id, title FROM openalex.works_all OFFSET :start LIMIT :batch;')
        res = session.execute(stmt, {'start': b, 'batch': BATCH})
        titles = res.mappings().all()
        for title in titles:
            # print(title['id'], title['title'])
            # print(title)
            p = model.predict(rg.sub(' ', title['title']), k=2)
            # print(p)
            print(f'{title["id"]}\t{p[0][0][9:]}\t{p[1][0]}\t{p[0][-1][9:]}\t{p[1][-1]}')
            # print(p)
            stats.append(p[0][0])
        # print(b, Counter(stats).most_common())

print(Counter(stats).most_common())
# 2800000 (works_filtered)
# ('__label__en', 2332336), -> 83.3%
# ('__label__es', 138108),
# ('__label__id', 94530),
# ('__label__fr', 85352),
# ('__label__pt', 83728),
# ('__label__de', 61217),
# ('__label__ja', 14407),
# ('__label__tr', 13636),
# ('__label__it', 10553),
# ('__label__cs', 10401),
# ('__label__sv', 8743),
# ('__label__pl', 7724),
# ('__label__nl', 6783),
# ('__label__ms', 5461),
# ('__label__hr', 4629),
# ('__label__ca', 3186),
# ('__label__hu', 2469),
# ('__label__zh', 2099),
# ('__label__sh', 1790),
# ('__label__sl', 1741),
# ('__label__no', 1163),
# ('__label__lt', 879),
# ('__label__sr', 849),
# ('__label__ru', 815),
# ('__label__ro', 755),
# ('__label__fi', 733),
# ('__label__sk', 717), ('__label__da', 686), ('__label__gl', 445), ('__label__af', 439), ('__label__eu', 409), ('__label__la', 355), ('__label__eo', 343), ('__label__bs', 308), ('__label__et', 247), ('__label__ko', 235), ('__label__ceb', 215), ('__label__lv', 133), ('__label__uk', 116), ('__label__az', 111), ('__label__vi', 108), ('__label__is', 86), ('__label__bn', 80), ('__label__el', 73), ('__label__tl', 57), ('__label__nn', 54), ('__label__ar', 41), ('__label__cy', 40), ('__label__sw', 39), ('__label__war', 36), ('__label__mk', 35), ('__label__fa', 34), ('__label__th', 31), ('__label__sq', 27), ('__label__oc', 27), ('__label__uz', 25), ('__label__fy', 24), ('__label__jv', 19), ('__label__hi', 19), ('__label__ga', 18), ('__label__br', 18), ('__label__mg', 17), ('__label__ku', 16), ('__label__nds', 14), ('__label__ast', 14), ('__label__ia', 11), ('__label__lb', 11), ('__label__kn', 10), ('__label__su', 10), ('__label__hy', 9), ('__label__ta', 9), ('__label__gd', 9), ('__label__ur', 9), ('__label__tt', 9), ('__label__bg', 8), ('__label__min', 8), ('__label__te', 7), ('__label__vo', 6), ('__label__io', 5), ('__label__mt', 5), ('__label__als', 5), ('__label__mr', 5), ('__label__ie', 4), ('__label__ml', 4), ('__label__an', 4), ('__label__sco', 3), ('__label__pms', 3), ('__label__wuu', 3), ('__label__he', 3), ('__label__be', 2), ('__label__bh', 2), ('__label__mn', 2), ('__label__ilo', 2), ('__label__mwl', 2), ('__label__jbo', 2), ('__label__lmo', 2), ('__label__my', 2), ('__label__wa', 2), ('__label__bar', 2), ('__label__eml', 1), ('__label__pam', 1), ('__label__so', 1), ('__label__qu', 1), ('__label__tk', 1), ('__label__or', 1), ('__label__diq', 1), ('__label__pa', 1), ('__label__cv', 1), ('__label__dsb', 1), ('__label__pnb', 1), ('__label__gn', 1), ('__label__kk', 1), ('__label__ne', 1), ('__label__bo', 1), ('__label__hsb', 1), ('__label__ht', 1), ('__label__ka', 1), ('__label__ug', 1), ('__label__as', 1), ('__label__si', 1), ('__label__ba', 1)]

# 4000000 (works_all)
# ('__label__en', 2464506), -> 61.61%
# ('__label__ja', 482076),
# ('__label__es', 215246),
# ('__label__de', 170730),
# ('__label__fr', 162546),
# ('__label__zh', 94928),
# ('__label__ko', 83450), ('__label__ru', 69412), ('__label__pt', 65032), ('__label__pl', 60803), ('__label__it', 52181), ('__label__nl', 26025), ('__label__id', 20703), ('__label__tr', 16538), ('__label__cs', 10781), ('__label__ar', 10628), ('__label__ca', 10592), ('__label__fa', 9623), ('__label__sv', 9502), ('__label__uk', 7327), ('__label__fi', 7287), ('__label__no', 5954), ('__label__el', 5140), ('__label__da', 5132), ('__label__hr', 4564), ('__label__hu', 3779), ('__label__lt', 2473), ('__label__ms', 1990), ('__label__sh', 1773), ('__label__ro', 1699), ('__label__sl', 1384), ('__label__gl', 1357), ('__label__la', 1292), ('__label__sr', 1099), ('__label__et', 1069), ('__label__th', 844), ('__label__vi', 835), ('__label__sk', 794), ('__label__eu', 725), ('__label__af', 685), ('__label__lv', 677), ('__label__hi', 558), ('__label__ka', 533), ('__label__bg', 492), ('__label__eo', 458), ('__label__bs', 368), ('__label__is', 359), ('__label__ceb', 357), ('__label__cy', 269), ('__label__nn', 267), ('__label__hy', 254), ('__label__he', 194), ('__label__be', 183), ('__label__arz', 182), ('__label__ga', 171), ('__label__az', 161), ('__label__ur', 141), ('__label__mk', 119), ('__label__bn', 114), ('__label__ta', 112), ('__label__kk', 112), ('__label__tl', 98), ('__label__sq', 89), ('__label__sa', 88), ('__label__mn', 77), ('__label__war', 63), ('__label__oc', 55), ('__label__ast', 54), ('__label__sw', 53), ('__label__fy', 52), ('__label__mt', 42), ('__label__uz', 39), ('__label__si', 38), ('__label__ckb', 38), ('__label__mr', 36), ('__label__dv', 32), ('__label__br', 27), ('__label__nds', 27), ('__label__ml', 25), ('__label__ia', 24), ('__label__te', 23), ('__label__ne', 22), ('__label__kn', 21), ('__label__tg', 19), ('__label__gd', 19), ('__label__wuu', 19), ('__label__lb', 17), ('__label__an', 14), ('__label__ba', 14), ('__label__gu', 14), ('__label__or', 14), ('__label__jv', 13), ('__label__pnb', 13), ('__label__io', 12), ('__label__su', 12), ('__label__ku', 12), ('__label__bo', 12), ('__label__als', 10), ('__label__ky', 9), ('__label__wa', 9), ('__label__ie', 8), ('__label__min', 8), ('__label__jbo', 7), ('__label__yi', 7), ('__label__ilo', 7), ('__label__sd', 6), ('__label__tt', 6), ('__label__azb', 5), ('__label__pa', 5), ('__label__ps', 5), ('__label__am', 4), ('__label__new', 4), ('__label__km', 4), ('__label__mg', 4), ('__label__my', 4), ('__label__lmo', 4), ('__label__gom', 4), ('__label__lo', 4), ('__label__qu', 4), ('__label__gn', 4), ('__label__sco', 3), ('__label__bh', 3), ('__label__hsb', 3), ('__label__yue', 3), ('__label__xmf', 3), ('__label__bar', 3), ('__label__eml', 3), ('__label__diq', 3), ('__label__pms', 3), ('__label__kw', 3), ('__label__cbk', 2), ('__label__vo', 2), ('__label__pam', 2), ('__label__yo', 2), ('__label__mzn', 2), ('__label__so', 2), ('__label__mwl', 2), ('__label__bpy', 1), ('__label__tk', 1), ('__label__scn', 1), ('__label__krc', 1), ('__label__li', 1), ('__label__cv', 1), ('__label__as', 1), ('__label__lez', 1), ('__label__rm', 1), ('__label__mhr', 1), ('__label__sah', 1), ('__label__ht', 1)]
