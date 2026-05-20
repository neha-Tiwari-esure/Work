# Run the Failure Analyser

This note explains what the analyser does and how to use it.

## What the analyser does

The analyser:
- reads the same Test Analytics token from `.env`
- uses the normal runtime settings from `config/settings.yaml`
- fetches failed test details from the Test Analytics APIs
- filters failures by reason such as `unknown` or `auto`
- groups related failures by message / stack trace patterns
- writes a separate Excel workbook with grouped failure analysis

## Before you run it

Make sure this file contains a valid token:

```text
.env
```

Update this line when needed:

```env
TEST_ANALYTICS_TOKEN=your_token_here
```

## Main analyser command

```bash
cd /path/to/TestAnalyticsSmartInsight
source .venv/bin/activate
python src/main.py --config config/settings.yaml --export-failure-analysis --failure-reason unknown
```

## Run analyser for a specific run name

```bash
cd /path/to/TestAnalyticsSmartInsight
source .venv/bin/activate
python src/main.py \
  --config config/settings.yaml \
  --run-name 'Regression_Claims_MOTOR' \
  --export-failure-analysis \
  --failure-reason unknown
```

## Run analyser for multiple failure reasons

```bash
python src/main.py \
  --config config/settings.yaml \
  --export-failure-analysis \
  --failure-reason unknown \
  --failure-reason auto
```

## Scope options

By default, failure analysis uses the full sprint scope.

### Latest run only

```bash
python src/main.py \
  --config config/settings.yaml \
  --export-failure-analysis \
  --failure-analysis-scope latest-run
```

### Last N runs

```bash
python src/main.py \
  --config config/settings.yaml \
  --export-failure-analysis \
  --failure-analysis-scope last-runs \
  --failure-analysis-run-limit 2
```

### One exact run id

```bash
python src/main.py \
  --config config/settings.yaml \
  --export-failure-analysis \
  --failure-analysis-run-id 123456
```

### Restrict by batch/version text

```bash
python src/main.py \
  --config config/settings.yaml \
  --export-failure-analysis \
  --failure-analysis-batch-contains '9.2.0-rc.1'
```

## What the analyser output contains

The analyser workbook groups failures and includes fields like:
- group name
- failure reason
- affected test count
- test names
- test case ids
- run names
- products
- bugs
- message
- stack traces

It also deduplicates repeated test-level failure details before grouping them.

## Output location

The analyser writes a separate workbook next to the main workbook output.

Example output names:

```text
data/output/.../Sprint-9_Motor_2026-05-19_001_9_2_0_rc_1_FailureAnalysis.xlsx
```

or similar names based on:
- selected run id
- selected batch text
- scope (`sprint`, `latest-run`, `last-runs`)

## Expected success message

If it succeeds, you should see output similar to:

```text
✅ Created failure analysis: data/output/.../SomeWorkbook_FailureAnalysis.xlsx
```

## Common reasons it may fail

### 1. Token/auth issue
If the token is expired or invalid, API requests may fail.

Fix:
- update `TEST_ANALYTICS_TOKEN` in `.env`
- run again

### 2. No matching runs
If the selected run name, run id, or batch text does not match the discovered sprint runs, the analyser may exit with a diagnostic.

Fix:
- check the exact run id / run name / batch text
- rerun with corrected values

### 3. No matching failure reasons
If there are no failures for the requested reason, the analyser may not create a workbook.

Fix:
- try another `--failure-reason`
- widen the scope

## Useful files

- `docs/RUN_MVP.md` - MVP run guide
- `docs/analyser.md` - this guide
- `config/settings.yaml` - runtime config
- `.env` - token location
- `src/main.py` - entry point
- `src/analysis/failure_analyzer.py` - grouping and deduplication logic
