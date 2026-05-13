# TestAnalytics API map

This file now separates two evidence levels clearly:
- exact request URLs confirmed from the exported Postman collection
- response shapes and supporting endpoints inferred from the live UI bundle

## Evidence sources
- Postman export: `data/postman/TestAnalytics.postman_collection.json`
- UI bundle evidence: public Next.js app and downloaded JS bundle analysis
- Important validation note: the auth values saved in the Postman export now return `401`, so request paths are exact, but live payload sampling still needs a fresh token or environment export

## Base URL
- `https://eis-analytics-v3-01.escloud.co.uk`

## Auth model
### Confirmed from Postman export
- Method style: `GET`
- Header: `accept: application/json`
- Header: `authorization: Bearer <token>`
- Browser-only headers also appeared in the export (`referer`, `sessionid`, `Cookie`, `sec-*`, `user-agent`), but these should not be treated as required for the Python client

### Recommended Python auth model
- Use only:
  - `Authorization: Bearer ${TEST_ANALYTICS_TOKEN}`
  - `Accept: application/json`
- Do not copy browser cookies into code

## Exact APIs confirmed from the Postman collection

### 1. Batch name lookup
- Postman request name: `ID`
- Method: `GET`
- Endpoint: `/api/batches/names`
- Query:
  - `id=<batch_uuid>`
- Sample exact request from export:
  - `GET https://eis-analytics-v3-01.escloud.co.uk/api/batches/names?id=d0b5b9a1-4039-11f1-84d2-41aed19e833d`
- Purpose:
  - resolve batch id to batch name
- Response shape inferred from UI usage:
  - object map keyed by batch id
  - example shape:
    ```json
    {
      "d0b5b9a1-4039-11f1-84d2-41aed19e833d": "<batch-name>"
    }
    ```

### 2. Run details plus counts and aggregations
- Postman request name: `Aggregations`
- Method: `GET`
- Endpoint: `/api/runs/{run_id}`
- Sample exact request from export:
  - `GET https://eis-analytics-v3-01.escloud.co.uk/api/runs/babe29a8-404d-11f1-84d2-855d0da06c64`
- Purpose:
  - fetch the main run object, counts, and aggregation metrics
- Response shape confirmed from UI bundle:
  ```json
  {
    "run": {
      "id": "<run_uuid>",
      "name": "<run name>",
      "status": "<status>",
      "started": "<iso datetime>",
      "finished": "<iso datetime>",
      "properties": {},
      "tags": [],
      "isProper": true,
      "effectiveDuration": 0,
      "mergeCount": 0,
      "createdBy": 0,
      "batchId": "<batch_uuid>"
    },
    "counts": {
      "total": 0,
      "incomplete": 0,
      "passRate": 0,
      "analysisRatio": 0,
      "statuses": {
        "passed": 0,
        "failed": 0,
        "skipped": 0
      },
      "reasons": {
        "auto": 0,
        "perf": 0,
        "unknown": 0,
        "in_analysis": 0,
        "prod": 0,
        "env": 0
      }
    },
    "aggregations": {
      "totalMethods": 0,
      "activeMethods": 0,
      "activeTests": 0,
      "totalMethodsPlainDuration": 0,
      "activeMethodsPlainDuration": 0,
      "activeTestsPlainDuration": 0,
      "totalMethodsEffectiveDuration": 0,
      "activeMethodsEffectiveDuration": 0,
      "activeTestsEffectiveDuration": 0,
      "mergedRunProps": {}
    }
  }
  ```
- UI flattening behavior:
  - UI rewrites this into `run` fields at top level and keeps `counts` and `aggregations`

### 3. Run brief rows
- Postman request name: `Breif` in export, typo preserved by Postman item name
- Method: `GET`
- Endpoint: `/api/runs/{run_id}/brief`
- Sample exact request from export:
  - `GET https://eis-analytics-v3-01.escloud.co.uk/api/runs/babe29a8-404d-11f1-84d2-855d0da06c64/brief`
- Purpose:
  - fetch brief breakdown rows used on the run details screen
- Response shape confirmed from UI bundle:
  - array
  - item schema still needs fresh live sampling

### 4. Run bugs
- Postman request name: `Bugs`
- Method: `GET`
- Endpoint: `/api/runs/{run_id}/bugs`
- Sample exact request from export:
  - `GET https://eis-analytics-v3-01.escloud.co.uk/api/runs/babe29a8-404d-11f1-84d2-855d0da06c64/bugs`
- Purpose:
  - fetch bugs linked to a run
- Response shape confirmed from UI bundle:
  - array
  - item schema still needs fresh live sampling

## Additional exact APIs discovered from the UI bundle
These were not in the exported collection, but the UI clearly calls them and they are useful for automation.

### 5. Runs for a batch
- Method: `GET`
- Endpoint: `/api/runs`
- Query used by UI:
  - `batchId=<batch_uuid>`
  - `page[num]=1`
  - `page[size]=100000`
  - `isProper=true` by default
- Purpose:
  - enumerate runs inside a batch so the extractor can inspect nightly candidates
- Response shape inferred from UI usage:
  ```json
  {
    "data": [
      {
        "id": "<run_uuid>",
        "name": "<run name>",
        "status": "<status>",
        "started": "<iso datetime>",
        "finished": "<iso datetime>",
        "properties": {},
        "tags": [],
        "isProper": true,
        "effectiveDuration": 0,
        "mergeCount": 0,
        "createdBy": 0,
        "batchId": "<batch_uuid>",
        "batchName": "<batch name>",
        "counts": {
          "total": 0,
          "incomplete": 0,
          "passRate": 0,
          "analysisRatio": 0,
          "statuses": {
            "passed": 0,
            "failed": 0,
            "skipped": 0
          },
          "reasons": {
            "auto": 0,
            "perf": 0,
            "unknown": 0,
            "in_analysis": 0,
            "prod": 0,
            "env": 0
          }
        }
      }
    ],
    "meta": {},
    "links": {}
  }
  ```

### 6. Run attachments
- Method: `GET`
- Endpoint: `/api/runs/{run_id}/attachments`
- Purpose:
  - optional, used by run details screen
- Not required for the Excel MVP

### 7. Run history
- Method: `GET`
- Endpoint: `/api/runs/{run_id}/history`
- Query used by UI:
  - `page[num]`
  - `page[size]`
- Purpose:
  - optional, useful later for trend views or regression comparisons

### 8. Run groups with ids
- Method: `GET`
- Endpoint: `/api/runs/{run_id}/groupsWithIds`
- Query used by UI:
  - filter params
  - `includeChildren=true`
  - `page[num]=1`
  - `page[size]=999999`
- Purpose:
  - optional deep drill-down, not needed for the sprint workbook MVP

## Practical request dependency chain for this project
1. Start with configured batch ids or discovered sprint batches
2. Resolve batch names via `GET /api/batches/names?id=<batch_id>`
3. Enumerate runs in each batch via `GET /api/runs?batchId=<batch_id>...`
4. Filter candidates either:
   - by exact `run_name` match when `--run-name` is supplied
   - or by nightly pattern plus optional product text heuristics in broad mode
5. Fetch each selected run via:
   - `GET /api/runs/{run_id}`
   - `GET /api/runs/{run_id}/brief`
   - `GET /api/runs/{run_id}/bugs`
6. Normalize the fields into Excel rows
7. Write one broad sprint workbook or one workbook per requested exact `run_name`

## Exact field mapping used by the Python extractor

### Core row fields
- `run_id` ← `run.id`
- `run_name` ← `run.name`
- `run_status` ← `run.status`
- `execution_datetime` ← `run.started`
- `finished_datetime` ← `run.finished`
- `duration` ← `run.effectiveDuration`
- `batch_id` ← `run.batchId`
- `batch_name` ← `run.batchName` or batch name lookup result
- `tags` ← `run.tags`
- `properties` ← `run.properties`

### Summary count fields
- `total_tests` ← `counts.total`
- `incomplete` ← `counts.incomplete`
- `pass_rate` ← `counts.passRate`
- `analysis_ratio` ← `counts.analysisRatio`
- `passed` ← `counts.statuses.passed`
- `failed` ← `counts.statuses.failed`
- `skipped` ← `counts.statuses.skipped`

### Failure reason fields
- `not_analysed` ← `counts.reasons.unknown`
- `in_analysis` ← `counts.reasons.in_analysis`
- `automation_issues` ← `counts.reasons.auto`
- `performance_issues` ← `counts.reasons.perf`
- `product_issues` ← `counts.reasons.prod`
- `environment_issues` ← `counts.reasons.env`

### Aggregation fields
- `total_methods` ← `aggregations.totalMethods`
- `active_methods` ← `aggregations.activeMethods`
- `active_tests` ← `aggregations.activeTests`
- `total_methods_plain_duration` ← `aggregations.totalMethodsPlainDuration`
- `active_methods_plain_duration` ← `aggregations.activeMethodsPlainDuration`
- `active_tests_plain_duration` ← `aggregations.activeTestsPlainDuration`
- `total_methods_effective_duration` ← `aggregations.totalMethodsEffectiveDuration`
- `active_methods_effective_duration` ← `aggregations.activeMethodsEffectiveDuration`
- `active_tests_effective_duration` ← `aggregations.activeTestsEffectiveDuration`

### Auxiliary fields
- `brief_rows` ← `len(brief_response_array)`
- `bug_count` ← `len(bugs_response_array)`

## Remaining live-validation gaps
Still needs a fresh token or active Postman environment export:
- actual item schema inside `/brief`
- actual item schema inside `/bugs`
- the best reliable product-identification field for `Claims Motor`
- confirmation that configured batch ids cover the sprint window you want

## Current implementation conclusion
The project now has enough exact endpoint mapping to replace the placeholder client paths and continue the Python MVP. The remaining blocker is not endpoint discovery anymore, it is live authenticated execution.