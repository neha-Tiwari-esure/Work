# TestAnalyticsSmartInsight

Agent-assisted extraction of EIS Test Analytics nightly regression data into sprint-based Excel reports.

## What this project is
This repo is for a Python-based helper agent that will:
- pull nightly regression data from EIS Test Analytics 3.0
- filter by product, for example `Claims Motor`
- optionally filter by one or more exact `run_name` values
- collect sprint-based run metrics
- write formatted Excel workbooks
- optionally generate short insights with Claude

## Current status
This is now a wired MVP that has completed a first live extraction run.

Already done:
- project structure created
- Postman collection added under `data/postman/`
- exact endpoint mapping documented from the Postman export
- supporting API flow inferred from the live UI bundle
- Python client updated to use the real discovered endpoints
- run normalization updated to use real `run`, `counts`, and `aggregations` fields
- config now supports automatic sprint batch discovery and run selection options
- CLI now supports exact `--run-name` filters, including multiple values in one command
- each requested exact `run_name` can now write its own workbook automatically
- missing exact `run_name` values now print a clear diagnostic instead of failing silently
- live workbooks generated successfully under `data/output/`

Still needed:
- live response sampling for `/brief` and `/bugs` item shapes
- confirmation of the best product-identification signal for `Claims Motor`
- replacement of the current temporary personal token with a dedicated QA user profile

## Project layout
```text
TestAnalyticsSmartInsight/
├── .env.example                   # secrets template, do not put real secrets in git
├── README.md                    # project overview and run instructions
├── requirements.txt              # Python dependencies
├── config/
│   └── settings.yaml             # main config, product filter, sprint window, batch ids, output path
├── data/
│   ├── postman/                  # exported Postman collection and environment
│   ├── raw/                      # optional raw API payload dumps or discovery artifacts
│   ├── processed/                # cleaned/intermediate files
│   └── output/                   # generated Excel files and insights output
├── docs/
│   ├── BUILD_PLAN.md             # build order and acceptance criteria
│   ├── LOCAL_POSTMAN_DISCOVERY.md # earlier local cache clues
│   └── testanalytics-api-map.md  # exact request and field mapping
├── scripts/
│   ├── setup.sh                  # create venv, install deps, prep local env
│   ├── run.sh                    # run the main script with the default config
│   └── inspect_postman_export.py # inspect an exported Postman collection JSON
├── src/
│   ├── main.py                   # main entry point
│   ├── client/
│   │   └── analytics_api.py      # HTTP client for Test Analytics APIs
│   ├── excel/
│   │   └── workbook_writer.py    # writes the Excel workbook
│   ├── insights/
│   │   └── claude_summary.py     # optional Claude summary stub
│   ├── extract/                  # reserved for dedicated extractors later
│   └── transform/
│       └── normalize_runs.py     # nightly filtering and row normalization
└── tests/
    └── README.md                 # placeholder for unit tests
```

## Config that matters now
### `config/settings.yaml`
The current MVP expects:
- `base_url`
- `product_filters`
- `run_name_patterns`
- `batch_ids`
- `run_selection.include_improper_runs`
- `run_selection.page_size`
- `bugs.include_bug_counts`
- `sprint.start`
- `sprint.end`
- `output.workbook_path`

### `.env`
Create this from `.env.example` and put secrets here:
- `TEST_ANALYTICS_TOKEN`
- username/password only if needed later
- `CLAUDE_API_KEY` if Claude gets wired later

Current local state:
- a temporary personal Test Analytics token is being used for development right now
- this should be replaced with a dedicated QA user profile later
- tracked follow-up: `docs/TODO.md`

## How to set it up
From the project folder:

```bash
cd /path/to/TestAnalyticsSmartInsight
bash scripts/setup.sh
```

## How to run it
### Default run
```bash
cd /path/to/TestAnalyticsSmartInsight
bash scripts/run.sh
```

### Direct Python run
```bash
cd /path/to/TestAnalyticsSmartInsight
source .venv/bin/activate
python src/main.py --config config/settings.yaml
```

### Exact `run_name` runs
Run one exact `run_name`:

```bash
python src/main.py --config config/settings.yaml --run-name 'Regression_Claims_MOTOR'
```

Run several exact `run_name` values and get one workbook per requested name:

```bash
python src/main.py --config config/settings.yaml \
  --run-name 'Regression_Claims_MOTOR' \
  --run-name 'Regression_Claims_HOME' \
  --run-name 'Claims_APP23_TESTS'
```

## What happens when you run it now
With a working `TEST_ANALYTICS_TOKEN`, the code will:
1. discover sprint batches from `GET /api/batches`
2. list runs for each matching batch
3. filter likely nightly regression runs, or exact `run_name` matches when requested
4. fetch exact run details, brief rows, and bug rows
5. normalize those into sprint rows
6. write one broad workbook or separate exact-name workbooks under `data/output/`

Current local result:
- `data/output/Sprint-XX-TestAnalytics.xlsx` was generated successfully for the broad sprint export
- exact `run_name` exports were also verified successfully:
  - `Regression_Claims_MOTOR` -> 4 sprint rows
  - `Claims_APP23_TESTS` -> 4 sprint rows
  - `Regression_Claims_HOME` -> 0 sprint rows in the current discovered sprint batches, with a diagnostic printed by the script

Without a working token, the request mapping is still useful, but the API calls will fail with `401`.

## Most important docs
- Exact API mapping: `docs/testanalytics-api-map.md`
- Build order: `docs/BUILD_PLAN.md`
- Earlier cache clues: `docs/LOCAL_POSTMAN_DISCOVERY.md`

## Best next step
1. Decide whether the default export should stay broad or move to exact `run_name` mode for Claims Core
2. Inspect the generated exact-name workbooks and confirm the row counts and columns are what you want
3. If `/brief` or `/bugs` need richer columns, sample one live response and extend the workbook schema
4. Replace the temporary personal token with a dedicated QA user profile, as noted in `docs/TODO.md`
