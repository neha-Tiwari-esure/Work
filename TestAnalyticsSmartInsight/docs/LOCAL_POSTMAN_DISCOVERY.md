# Local Postman discovery notes

These notes were recovered from your local Postman cache, not from a clean export.
That means they are useful clues, but they are not the final source of truth.

## Confirmed local paths
- Postman app: `/Applications/Postman.app`
- Main local data: `~/Library/Application Support/Postman`
- Active signed-in user partition observed:
  - `~/Library/Application Support/Postman/Partitions/dff9dd5e-73fa-4a92-99a9-b67ef91b817c`

## Confirmed collection
- Collection name: `TestAnalytics`
- Collection uid seen locally:
  - `-46227564-1e26c9cb-210a-4893-9031-939c1b8e42f6`

## Confirmed endpoint clues
Observed in local cache:
- `GET https://eis-analytics-v3-01.escloud.co.uk/api/batches/names?id=d0b5b9a1-4039-11f1-84d2-41aed19e833d`
- `GET https://eis-analytics-v3-01.escloud.co.uk/api/runs/babe29a8-404d-11f1-84d2-855d0da06c64`
- `GET https://eis-analytics-v3-01.escloud.co.uk/api/runs/babe29a8-404d-11f1-84d2-855d0da06c64/brief`
- `GET https://eis-analytics-v3-01.escloud.co.uk/api/runs/babe29a8-404d-11f1-84d2-855d0da06c64/bugs`

## Confirmed request/editor labels
- `Aggregations`
- `Bugs`

## Important safety note
A bearer token was present in local cache while inspecting these clues.
It was intentionally not copied into this repo or any docs.
Keep secrets only in `.env` or secure local auth flows.

## What to do with this
Use these clues to speed up the clean mapping step, but treat the exported collection JSON plus live responses as the final reference.
