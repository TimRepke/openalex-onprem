import httpx

with open('data/climate_health_ids.txt') as f:
    openalex_ids = set(f.readlines())

with httpx.AsyncClient() as client:
    pass