# Captured API responses

Each `.json` here is a real response body from one of the upstream APIs the
plugin talks to. Tests read these instead of hitting the live API so they stay
fast, offline, and deterministic.

When an upstream API drifts, refetch the fixture by running the command in the
`source` field below and saving the response in place. Add a note in the
plugin's CHANGELOG so future-you knows when the schema shifted.

## Files

| File | Source | Captured |
|---|---|---|
| `lakes_worker_caspian.json` | `curl 'https://lakes.swot-lake.workers.dev/?q=caspian'` | 2026-05-26 |
| `hydrocron_reach_response.json` | `curl 'https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=23261000181&start_time=2024-01-01T00:00:00Z&end_time=2024-02-01T00:00:00Z&fields=reach_id,time_str,wse,width&output=geojson'` | hand-trimmed sample |
