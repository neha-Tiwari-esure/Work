# Exact build plan

## Phase 1, discovery in Postman
- Export `TestAnalytics.postman_collection.json`
- Export active Postman environment JSON
- Confirm the request purpose for:
  - `ID`
  - `Aggregations`
  - `Brief`
  - `Bugs`
- Record:
  - method
  - endpoint
  - headers
  - auth model
  - query params
  - sample response
  - field mappings

## Phase 2, API mapping document
Create `docs/testanalytics-api-map.md` with:
- request name
- endpoint purpose
- sample request
- sample response
- required output fields
- request dependencies

## Phase 3, Python MVP
Deliver an MVP that:
- reads config
- calls real endpoints
- filters nightly runs for one product or by exact `run_name`
- extracts:
  - run name
  - execution date/time
  - duration
  - total tests
  - passed
  - failed
  - not analysed
- writes one Excel workbook per sprint, or one workbook per requested exact `run_name`

## Phase 4, Excel enhancements
Add:
- formatting
- summary sheet
- charts
- failure detail sheet
- bugs sheet

## Phase 5, Claude insights
Generate concise insights from processed summary data:
- latest run health
- repeated failures
- trend changes
- bug hotspots

## Phase 6, automation
Run twice a week with a scheduler.

## MVP acceptance criteria
- One command produces a valid workbook
- Broad sprint export writes a valid workbook under `data/output/`
- Exact `run_name` export mode writes one workbook per requested name
- Missing exact `run_name` values print a clear diagnostic
- Pass/fail/not analysed numbers match API data
