
PREPARE nodes(text) AS

    SELECT json_build_object('nodes',
                json_agg(
                    json_build_object('id',t.title)
                    )
                )
    FROM (
	    SELECT a.title
	    FROM openalex.works_filtered a
	    WHERE a.id = $1
	    UNION
	    SELECT b.title
	    FROM openalex.works_referenced_works a
	    JOIN openalex.works_filtered b
	    ON a.referenced_work_id = b.id
	    WHERE a.work_id = $1
	    ) t;

PREPARE links(text) AS

SELECT json_build_object('links',
            json_agg(
                json_build_object('source',t.source,'target',t.target,'value',t.val)
                )
            )
    FROM (
    	SELECT
    	a.title as "source", c.title as "target", SUM(1) as "val"
    	FROM openalex.works_filtered a
    	LEFT JOIN openalex.works_referenced_works b
    	ON a.id = b.work_id
    	LEFT JOIN openalex.works_filtered c
    	ON b.referenced_work_id = c.id
    	WHERE a.id = $1
    	GROUP BY 1,2
      ) t;

EXECUTE nodes(:'oa_id');
EXECUTE links(:'oa_id');
