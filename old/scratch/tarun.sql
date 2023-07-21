
-- TITLE-ABS-KEY(
--        (   household*
--         OR residential
--         OR building
--         OR dormitor*
--         OR individual
--         OR consumer*
--         OR participant*
--         OR customer*
--         OR domestic
--         OR homeowner*
--        )
--    AND (   feedback
--         OR pric*
--         OR {time-of-use}
--         OR {time-of-day}
--         OR {real time}
--         OR {peak}
--         OR {dynamic pricing}
--         OR "smart meter*"
--         OR "smart grid*"
--         OR (    behavioral
--             AND (   economic*
--                  OR intervention*
--                  OR guideline*
--                 )
--            )
--         OR nudge*
--         OR {choice architecture}
--         OR norm
--         OR norms
--         OR {normative}
--         OR {social influence}
--         OR {block leader}
--         OR {public commitment}
--         OR {social comparison}
--         OR {social learning}
--         OR {social modeling}
--         OR {peer comparison}
--         OR {peer information}
--         OR salience
--         OR "commitment device*"
--         OR {Pre-commitment}
--         OR {precommitment}
--         OR pledge
--         OR {behavioral contract}
--         OR {commitment contract}
--         OR "commitment approach*"
--         OR {personal commitment}
--         OR audit OR rebate
--         OR reward
--         OR incentives
--         OR {goal setting}
--         OR {home energy report}
--         OR {in-home display}
--         OR (    information
--             W/3 (   campaign*
--                  OR provision
--                  OR strategies
--                  OR acquisition
--                  OR intervention*
--                  OR system*)
--                 )
--             OR {foot-in-the-door}
--             OR {minimal justification}
--             OR "applied game*"
--             OR "serious game*"
--             OR gamif*
--             OR {dissonance}
--             OR tariff
--             OR "time-varying pricing"
--          )
--      AND (
--                  (
--                    (   energy
--                     OR electric*
--                     OR gas
--                    )
--                    W/15 (   consumption
--                          OR conservation
--                          OR efficiency
--                          OR use
--                          OR demand
--                          OR usage
--                         )
--                    )
--                  OR "price responsiveness"
--                )
--  )


--    Population
--  ((household* OR residential OR building OR dormitor* OR individual OR consumer* OR participant* OR customer* OR domestic OR homeowner*)
--    Intervention
--  (feedback OR pric* OR {time-of-use} OR {time-of-day} OR {real time} OR {peak} OR {dynamic pricing} OR "smart meter*" OR "smart grid*" OR (behavioral AND (economic* OR intervention* OR guideline*)) OR nudge* OR {choice architecture} OR norm OR norms or {normative} OR {social influence} OR {block leader} OR {public commitment} OR {social comparison} OR {social learning} OR {social modeling} OR {peer comparison} OR {peer information} OR salience OR "commitment device*" OR {Pre-commitment} OR {precommitment} OR pledge OR {behavioral contract} OR {commitment contract} OR "commitment approach*" OR {personal commitment} OR audit OR rebate OR reward OR incentives OR {goal setting} OR {home energy report} OR {in-home display} OR (information W/3 (campaign* OR provision OR strategies OR acquisition OR intervention* OR system*)) OR {foot-in-the-door} OR {minimal justification} OR "applied game*" OR "serious game*" OR gamif* OR {dissonance} OR tariff OR "time-varying pricing")
--    Comparator
--  -
--    Outcome
--  (((energy OR electric* OR gas) W/15 (consumption OR conservation OR efficiency OR use OR demand OR usage)) OR "price responsiveness"))
--    Study type
--  -
--    Note: Since JSTOR and Publish or Perish do not allow for long search strings, a simplified query was run on these databases: (information OR feedback OR price OR incentives) AND (household* OR residential) AND ("electricity consumption" OR "energy consumption" or "energy conservation").


-- Nature Energy
SELECT *
FROM openalex.works_filtered a
         LEFT JOIN openalex.abstracts b ON a.id = b.id
WHERE (to_tsvector('english', a.title) || to_tsvector('english', b.abstract)) @@
      ('' ||
           -- population
       '  (  household:* | residential | building | dormitor:* | individual ' ||
       '   | consumer:* | participant:* | customer:* | domestic | homeowner:* ' ||
       '  ) ' ||
           -- intervention
       '& (  feedback | pric:* | time-of-use | time<->of<->use | time-of-day | time<->of<->day | real<->time | peak ' ||
       '   | dynamic<->pricing | smart<->meter:* | smart<->grid:* ' ||
       '   | (behavioral & (economic:* | intervention:* | guideline:*)) | nudge:* | choice<->architecture | norm | norms ' ||
       '   | normative | social<->influence | block<->leader | public<->commitment | social<->comparison | social<->learning ' ||
       '   | social<->modeling | peer<->comparison | peer<->information | salience | commitment<->device:* ' ||
       '   | Pre-commitment | precommitment | pledge | behavioral<->contract | commitment<->contract | commitment<->approach:* ' ||
       '   | personal<->commitment | audit | rebate | reward | incentives | goal<->setting | home<->energy<->report | in-home<->display ' ||
       '   | ( information <3> ( campaign:* | provision | strategies | acquisition | intervention:* | system:* ) ) ' ||
       '   | foot-in-the-door | minimal<->justification | applied<->game:* | serious<->game:* | gamif:* ' ||
       '   | dissonance | tariff | (time-varying | time<->varying)<->pricing ' ||
       '  )' ||
           -- outcome
       '& ( price <-> responsiveness ' ||
       '   | ( ' ||
       '       ( energy | electric:* | gas ) ' ||
       '        <15> ' ||
       '       ( consumption | conservation | efficiency | use | demand | usage) ' ||
       '     ) ' ||
       '  )')::tsquery
LIMIT 5;


EXPLAIN ANALYSE
SELECT count(1)
FROM (SELECT a.id
      FROM openalex.works_filtered a
      WHERE to_tsvector('english', a.title) @@ ('' ||
           -- population
       '  (  household:* | residential | building | dormitor:* | individual ' ||
       '   | consumer:* | participant:* | customer:* | domestic | homeowner:* ' ||
       '  ) ' ||
           -- intervention
       '& (  feedback | pric:* | time-of-use | time<->of<->use | time-of-day | time<->of<->day | real<->time | peak ' ||
       '   | dynamic<->pricing | smart<->meter:* | smart<->grid:* ' ||
       '   | (behavioral & (economic:* | intervention:* | guideline:*)) | nudge:* | choice<->architecture | norm | norms ' ||
       '   | normative | social<->influence | block<->leader | public<->commitment | social<->comparison | social<->learning ' ||
       '   | social<->modeling | peer<->comparison | peer<->information | salience | commitment<->device:* ' ||
       '   | Pre-commitment | precommitment | pledge | behavioral<->contract | commitment<->contract | commitment<->approach:* ' ||
       '   | personal<->commitment | audit | rebate | reward | incentives | goal<->setting | home<->energy<->report | in-home<->display ' ||
       '   | ( information <3> ( campaign:* | provision | strategies | acquisition | intervention:* | system:* ) ) ' ||
       '   | foot-in-the-door | minimal<->justification | applied<->game:* | serious<->game:* | gamif:* ' ||
       '   | dissonance | tariff | (time-varying | time<->varying)<->pricing ' ||
       '  )' ||
           -- outcome
       '& ( price <-> responsiveness ' ||
       '   | ( ' ||
       '       ( energy | electric:* | gas ) ' ||
       '        <15> ' ||
       '       ( consumption | conservation | efficiency | use | demand | usage) ' ||
       '     ) ' ||
       '  )')::tsquery

      UNION

      SELECT b.id
      FROM openalex.abstracts b
      WHERE b.ts_abstract @@ ('' ||
           -- population
       '  (  household:* | residential | building | dormitor:* | individual ' ||
       '   | consumer:* | participant:* | customer:* | domestic | homeowner:* ' ||
       '  ) ' ||
           -- intervention
       '& (  feedback | pric:* | time-of-use | time<->of<->use | time-of-day | time<->of<->day | real<->time | peak ' ||
       '   | dynamic<->pricing | smart<->meter:* | smart<->grid:* ' ||
       '   | (behavioral & (economic:* | intervention:* | guideline:*)) | nudge:* | choice<->architecture | norm | norms ' ||
       '   | normative | social<->influence | block<->leader | public<->commitment | social<->comparison | social<->learning ' ||
       '   | social<->modeling | peer<->comparison | peer<->information | salience | commitment<->device:* ' ||
       '   | Pre-commitment | precommitment | pledge | behavioral<->contract | commitment<->contract | commitment<->approach:* ' ||
       '   | personal<->commitment | audit | rebate | reward | incentives | goal<->setting | home<->energy<->report | in-home<->display ' ||
       '   | ( information <3> ( campaign:* | provision | strategies | acquisition | intervention:* | system:* ) ) ' ||
       '   | foot-in-the-door | minimal<->justification | applied<->game:* | serious<->game:* | gamif:* ' ||
       '   | dissonance | tariff | (time-varying | time<->varying)<->pricing ' ||
       '  )' ||
           -- outcome
       '& ( price <-> responsiveness ' ||
       '   | ( ' ||
       '       ( energy | electric:* | gas ) ' ||
       '        <15> ' ||
       '       ( consumption | conservation | efficiency | use | demand | usage) ' ||
       '     ) ' ||
       '  )')::tsquery) e;

-- SELECT w.id, w.doi, w.title, display_name, publication_year, publication_date, type, cited_by_api_url, cited_by_count, is_retracted, abstract
SELECT count(1)
FROM (SELECT a.id
      FROM openalex.works_filtered a
      WHERE to_tsvector('simple', a.title) @@ ('' ||
           -- population
       '  (  household:* | residential | building | dormitor:* | individual ' ||
       '   | consumer:* | participant:* | customer:* | domestic | homeowner:* ' ||
       '  ) ' ||
           -- intervention
       '& (  feedback | pric:* | time-of-use | time<->of<->use | time-of-day | time<->of<->day | real<->time | peak ' ||
       '   | dynamic<->pricing | smart<->meter:* | smart<->grid:* ' ||
       '   | (behavioral & (economic:* | intervention:* | guideline:*)) | nudge:* | choice<->architecture | norm | norms ' ||
       '   | normative | social<->influence | block<->leader | public<->commitment | social<->comparison | social<->learning ' ||
       '   | social<->modeling | peer<->comparison | peer<->information | salience | commitment<->device:* ' ||
       '   | Pre-commitment | precommitment | pledge | behavioral<->contract | commitment<->contract | commitment<->approach:* ' ||
       '   | personal<->commitment | audit | rebate | reward | incentives | goal<->setting | home<->energy<->report | in-home<->display ' ||
       '   | ( information <3> ( campaign:* | provision | strategies | acquisition | intervention:* | system:* ) ) ' ||
       '   | foot-in-the-door | minimal<->justification | applied<->game:* | serious<->game:* | gamif:* ' ||
       '   | dissonance | tariff | (time-varying | time<->varying)<->pricing ' ||
       '  )' ||
           -- outcome
       '& ( price <-> responsiveness ' ||
       '   | ( ' ||
       '       ( energy | electric:* | gas ) ' ||
       '        <15> ' ||
       '       ( consumption | conservation | efficiency | use | demand | usage) ' ||
       '     ) ' ||
       '  )')::tsquery

      UNION

      SELECT b.id
      FROM openalex.abstracts b
      WHERE to_tsvector('simple', b.abstract) @@ ('' ||
           -- population
       '  (  household:* | residential | building | dormitor:* | individual ' ||
       '   | consumer:* | participant:* | customer:* | domestic | homeowner:* ' ||
       '  ) ' ||
           -- intervention
       '& (  feedback | pric:* | time-of-use | time<->of<->use | time-of-day | time<->of<->day | real<->time | peak ' ||
       '   | dynamic<->pricing | smart<->meter:* | smart<->grid:* ' ||
       '   | (behavioral & (economic:* | intervention:* | guideline:*)) | nudge:* | choice<->architecture | norm | norms ' ||
       '   | normative | social<->influence | block<->leader | public<->commitment | social<->comparison | social<->learning ' ||
       '   | social<->modeling | peer<->comparison | peer<->information | salience | commitment<->device:* ' ||
       '   | Pre-commitment | precommitment | pledge | behavioral<->contract | commitment<->contract | commitment<->approach:* ' ||
       '   | personal<->commitment | audit | rebate | reward | incentives | goal<->setting | home<->energy<->report | in-home<->display ' ||
       '   | ( information <3> ( campaign:* | provision | strategies | acquisition | intervention:* | system:* ) ) ' ||
       '   | foot-in-the-door | minimal<->justification | applied<->game:* | serious<->game:* | gamif:* ' ||
       '   | dissonance | tariff | (time-varying | time<->varying)<->pricing ' ||
       '  )' ||
           -- outcome
       '& ( price <-> responsiveness ' ||
       '   | ( ' ||
       '       ( energy | electric:* | gas ) ' ||
       '        <15> ' ||
       '       ( consumption | conservation | efficiency | use | demand | usage) ' ||
       '     ) ' ||
       '  )')::tsquery) e
-- LEFT JOIN openalex.works_filtered w on e.id = w.id
-- LEFT JOIN openalex.abstracts ab on ab.id = w.id;
