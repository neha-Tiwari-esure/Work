# Run the TestAnalytics MVP

This note explains how to run the current MVP and where it writes the Excel output.

## What the MVP does

The MVP:
- loads the Test Analytics token from `.env`
- reads runtime settings from `config/settings.yaml`
- calls the Test Analytics APIs
- filters sprint/nightly regression runs
- writes an Excel workbook to `data/output/`

## Before you run it

Make sure this file contains a valid token:

```text
.env
```

Update this line when needed:

```env
TEST_ANALYTICS_TOKEN=your_token_here
```

## Main run command

```bash
cd /path/to/TestAnalyticsSmartInsight
bash scripts/run.sh
```

## Direct Python run

If you want to run it manually without the wrapper script:

```bash
cd /path/to/TestAnalyticsSmartInsight
source .venv/bin/activate
python src/main.py --config config/settings.yaml
```

## Run for one exact run_name

You can now target one exact `run_name` from the command line.

Example:

```bash
cd /path/to/TestAnalyticsSmartInsight
source .venv/bin/activate
python src/main.py --config config/settings.yaml --run-name 'Regression_Claims_MOTOR'
```

## Run for a specific sprint

If you want to target a sprint directly from the command line, pass `--sprint-name`.
The script will calculate the 14-day sprint window from the built-in base sprint reference.

Example:

```bash
cd /path/to/TestAnalyticsSmartInsight
source .venv/bin/activate
python src/main.py --config config/settings.yaml --sprint-name 'Sprint-9'
```

You can combine it with an exact run name too:

```bash
python src/main.py --config config/settings.yaml --sprint-name 'Sprint-9' --run-name 'REGRESSION_CLAIMS_MOTOR'
```

If you want to force exact dates from the command line, use:

```bash
python src/main.py --config config/settings.yaml --sprint-name 'Sprint-9' --sprint-start '2026-05-06' --sprint-end '2026-05-19'
```

If you pass one `--run-name` and do not pass `--output`, the script will automatically create a separate workbook name by appending the run name to the configured output filename.

## Run the 3 requested outputs

You can now request all 3 names in one command and the script will create 3 separate workbook files automatically.

```bash
cd /path/to/TestAnalyticsSmartInsight
source .venv/bin/activate
python src/main.py --config config/settings.yaml \
  --run-name 'Regression_Claims_MOTOR' \
  --run-name 'Regression_Claims_HOME' \
  --run-name 'Claims_APP23_TESTS'
```

That will create:

- `data/output/Sprint-XX-TestAnalytics-Regression_Claims_MOTOR.xlsx`
- `data/output/Sprint-XX-TestAnalytics-Regression_Claims_HOME.xlsx`
- `data/output/Sprint-XX-TestAnalytics-Claims_APP23_TESTS.xlsx`

If one requested `run_name` does not exist in the sprint window, the script will still write the workbook and print a diagnostic with the closest available `run_name` values.

You can also run them individually:

```bash
python src/main.py --config config/settings.yaml --run-name 'Regression_Claims_MOTOR'
python src/main.py --config config/settings.yaml --run-name 'Regression_Claims_HOME'
python src/main.py --config config/settings.yaml --run-name 'Claims_APP23_TESTS'
```

Or choose an exact output path manually for a single run:

```bash
python src/main.py --config config/settings.yaml --run-name 'Regression_Claims_MOTOR' --output 'data/output/Regression_Claims_MOTOR.xlsx'
```

## Output location

The workbook base path is configured in:

```text
config/settings.yaml
```

Current config key:

```yaml
output:
  workbook_path: "data/output/workbook.xlsx"
```

The main script now writes dated, product-specific workbooks under `data/output/YYYY-MM-DD/`.
The config value is mainly used as a base path for optional insight output and compatibility with older flow assumptions.

## Expected success message

If the default broad run succeeds, you should see output similar to:

```text
Workbook written to data/output/Sprint-XX-TestAnalytics.xlsx
Runs matched before sprint filtering: ...
Runs written for sprint window: ...
```

If you run with multiple exact `--run-name` values, you should see one `Workbook written to ...` line per requested name, plus totals at the end.

## How the token is used

The token is read from `.env` like this:

1. `src/main.py` calls `load_dotenv()`
2. `src/client/analytics_api.py` reads `TEST_ANALYTICS_TOKEN`
3. the API client sends it as a Bearer token in the `Authorization` header

## Common reasons it may fail

### 1. Token/auth issue
If the token is expired or invalid, API requests may fail with `401`.

Fix:
- update `TEST_ANALYTICS_TOKEN` in `.env`
- run again

### 2. Python SSL / urllib3 environment issue
If the local Python environment is old, you may see SSL or `urllib3` warnings/errors.

If that happens, refresh the virtual environment with a newer Python.

## Quick use checklist

1. Open `.env`
2. Update `TEST_ANALYTICS_TOKEN`
3. Run either the current sprint automatically:
   ```bash
   cd /path/to/TestAnalyticsSmartInsight
   bash scripts/run.sh
   ```
   or a specific sprint:
   ```bash
   python src/main.py --config config/settings.yaml --sprint-name 'Sprint-9'
   ```
4. Open the generated workbook in `data/output/YYYY-MM-DD/`

## Useful files

- `docs/RUN_MVP.md` - this guide
- `README.md` - project overview
- `config/settings.yaml` - runtime config
- `.env` - token location
- `scripts/run.sh` - main run command
- `src/main.py` - entry point
