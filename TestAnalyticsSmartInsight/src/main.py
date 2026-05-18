from __future__ import annotations

import argparse
import re
import os
from collections import Counter
from datetime import datetime, timedelta
from difflib import get_close_matches
from pathlib import Path

import yaml
from dotenv import load_dotenv

from client.analytics_api import client_from_env
from excel.workbook_writer import write_workbook
from insights.claude_summary import generate_insights
from transform.normalize_runs import (
    derive_product_label,
    filter_runs_for_sprint,
    looks_like_nightly,
    matches_exact_run_names,
    matches_product_filters,
    normalize_run_record,
)


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def is_within_sprint(raw_datetime: str, sprint_start: str, sprint_end: str) -> bool:
    if not raw_datetime:
        return False
    try:
        dt = datetime.fromisoformat(str(raw_datetime).replace("Z", "+00:00"))
    except ValueError:
        return False
    start = datetime.fromisoformat(sprint_start)
    end = datetime.fromisoformat(sprint_end)
    return start <= dt.replace(tzinfo=None) <= end


def _slugify_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
    cleaned = cleaned.strip("_")
    return cleaned or "run"


def _build_output_path(base_output_path: str, run_name: str) -> str:
    output_file = Path(base_output_path)
    return str(output_file.with_name(f"{output_file.stem}-{_slugify_filename(run_name)}{output_file.suffix}"))


def _print_missing_run_name_diagnostics(requested_names: list[str], available_run_names: list[str]) -> None:
    if not requested_names:
        return

    available_counter = Counter(name for name in available_run_names if name)
    available_unique = sorted(available_counter)
    normalized_available = {name.strip().lower(): name for name in available_unique}

    for requested_name in requested_names:
        normalized_requested = requested_name.strip().lower()
        if normalized_requested in normalized_available:
            continue

        print(f"No runs matched exact run_name: {requested_name}")
        suggestions = get_close_matches(requested_name, available_unique, n=5, cutoff=0.45)
        if suggestions:
            print("Closest available run_name values:")
            for suggestion in suggestions:
                print(f"  - {suggestion} ({available_counter[suggestion]} run(s))")
        else:
            print("No close run_name alternatives were found in the discovered sprint batches.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/settings.yaml")
    parser.add_argument("--run-name", action="append", default=[], help="Exact run_name to include. Repeat for multiple values.")
    parser.add_argument("--output", help="Optional workbook output path override.")
    args = parser.parse_args()

    load_dotenv()
    config = load_config(args.config)

    client = client_from_env(config["base_url"])
    if not client.token:
        raise SystemExit("TEST_ANALYTICS_TOKEN is missing. Add it to .env before running.")

    # ✅ Get sprint name safely
    sprint_name = config.get("sprint", {}).get("name", "Sprint")
    patterns = config.get("run_name_patterns", ["nightly"])
    exact_run_names = args.run_name or config.get("exact_run_names", [])
    product_filters = config.get("product_filters", [])
    sprint = config["sprint"]
    base_output_path = args.output or config["output"]["workbook_path"]
    batch_ids = config.get("batch_ids", [])
    batch_discovery = config.get("batch_discovery", {})
    run_selection = config.get("run_selection", {})
    include_improper_runs = run_selection.get("include_improper_runs", False)
    page_size = run_selection.get("page_size", 100000)
    include_bug_counts = config.get("bugs", {}).get("include_bug_counts", True)


    # ✅ Get sprint config
    sprint_config = config.get("sprint", {})
    manual_sprint_name = sprint_config.get("name")

    # ✅ Base sprint reference (YOU SET THIS ONCE)
    base_sprint_start = datetime(2026, 1, 28)
    base_sprint_number = 2   # adjust to your org

    # ✅ CASE 1 → manual sprint provided (e.g. Sprint-101)
    if manual_sprint_name and "XX" not in manual_sprint_name:

        sprint_name = manual_sprint_name
        sprint_number = int(sprint_name.split("-")[1])

        sprints_between = sprint_number - base_sprint_number

        sprint_start_date = base_sprint_start + timedelta(days=14 * sprints_between)
        sprint_end_date = sprint_start_date + timedelta(days=13)

    # ✅ CASE 2 → auto calculate current sprint
    else:
        today = datetime.now()

        days_passed = (today - base_sprint_start).days
        sprint_number = base_sprint_number + (days_passed // 14)

        sprint_name = f"Sprint-{sprint_number}"

        sprint_start_date = base_sprint_start + timedelta(days=14 * (sprint_number - base_sprint_number))
        sprint_end_date = sprint_start_date + timedelta(days=13)

    print("✅ Sprint:", sprint_name)
    print("✅ Start:", sprint_start_date.date())
    print("✅ End:", sprint_end_date.date())

    if batch_discovery.get("enabled"):
        batch_page_size = int(batch_discovery.get("page_size", 20))
        batch_max_pages = int(batch_discovery.get("max_pages", 10))
        batch_name_patterns = batch_discovery.get("name_patterns", ["test regression"])
        batch_ids = []

        for page_num in range(1, batch_max_pages + 1):
            discovered_batches = client.get_batches(page_num=page_num, page_size=batch_page_size)
            if not discovered_batches:
                break

            found_in_page = []
            for batch in discovered_batches:
                batch_id = batch.get("id")
                batch_name = str(batch.get("name") or "")
                created = batch.get("created") or ""
                if not batch_id:
                    continue
                if is_within_sprint(created, sprint["start"], sprint["end"]) and looks_like_nightly(
                    batch_name,
                    patterns=batch_name_patterns,
                ):
                    found_in_page.append(batch_id)

            batch_ids.extend(found_in_page)

            oldest_created = discovered_batches[-1].get("created") or ""
            if oldest_created and not is_within_sprint(oldest_created, sprint["start"], sprint["end"]):
                break

    if not batch_ids:
        raise SystemExit("No batch_ids configured or discovered for the sprint window.")

    batch_name_map = client.get_batch_names(batch_ids)
    normalized_rows = []
    available_run_names = []

    for batch_id in batch_ids:
        batch_name = batch_name_map.get(batch_id, "")
        candidate_runs = client.get_runs_for_batch(
            batch_id,
            include_improper_runs=include_improper_runs,
            page_size=page_size,
        )

        for candidate in candidate_runs:
            run_id = str(candidate.get("id") or "")
            run_name = str(candidate.get("name") or "")
            candidate_batch_name = str(candidate.get("batchName") or batch_name or "")
            if run_name:
                available_run_names.append(run_name)
            if not run_id:
                continue
            if exact_run_names:
                if not matches_exact_run_names(run_name, exact_run_names):
                    continue
            elif not looks_like_nightly(run_name, candidate_batch_name, patterns=patterns):
                continue

            run_payload = client.get_run(run_id)
            if not matches_product_filters(
                product_filters,
                run_summary=candidate,
                run_payload=run_payload,
                batch_name=candidate_batch_name,
            ):
                continue

            brief = client.get_brief(run_id)
            bugs = client.get_bugs(run_id) if include_bug_counts else []
            product_label = derive_product_label(
                product_filters,
                run_summary=candidate,
                run_payload=run_payload,
                batch_name=candidate_batch_name,
            )

            normalized_rows.append(
                normalize_run_record(
                    product=product_label or candidate_batch_name or run_name,
                    run_payload=run_payload,
                    brief_payload=brief,
                    bugs_payload=bugs,
                    batch_name=candidate_batch_name,
                    batch_id=batch_id,
                )
            )

    sprint_rows = filter_runs_for_sprint(
        normalized_rows,
        sprint_start=sprint_start_date.isoformat(),
        sprint_end=sprint_end_date.isoformat(),
    )

    date_str = datetime.now().strftime("%Y-%m-%d")
    output_dir = Path("data/output") / date_str
    output_dir.mkdir(parents=True, exist_ok=True)

# ✅ Create containers for each product
    home_rows = []
    motor_rows = []
    app23_rows = []

    for row in sprint_rows:

        run_name = str(
            row.get("name") or
            row.get("run_name") or
            ""
        ).strip().lower()

        print("RUN:", run_name)

        if "home" in run_name:
            home_rows.append(row)

        elif "motor" in run_name:
            motor_rows.append(row)

        elif "app23" in run_name or "app_23" in run_name:
            app23_rows.append(row)

        else:
            print("SKIPPED:", run_name)


    
    existing_files = os.listdir(output_dir)

    seq_num = 0

    for f in existing_files:
        if not f.endswith(".xlsx"):
            continue

        parts = f.replace(".xlsx", "").split("_")

    # ✅ Look for last part as number
        last_part = parts[-1]

        if last_part.isdigit() and len(last_part) == 3:
            seq_num = max(seq_num, int(last_part))

# ✅ increment for this run
    seq_num += 1

    seq = f"{seq_num:03d}"

    if home_rows:
        file_path = output_dir / f"{sprint_name}_Home_{date_str}_{seq}.xlsx"
        best_home = max(home_rows, key=lambda x: x.get("pass_rate", 0)) if home_rows else None
        write_workbook(home_rows, str(file_path), best_run=best_home)
        print("✅ Created:", file_path)

# ✅ Write MOTOR Excel
    if motor_rows:
        file_path = output_dir / f"{sprint_name}_Motor_{date_str}_{seq}.xlsx"
        best_motor = max(motor_rows, key=lambda x: x.get("pass_rate", 0)) if motor_rows else None
        write_workbook(motor_rows, str(file_path), best_run=best_motor)
        print("✅ Created:", file_path)

# ✅ Write APP23 Excel
    if app23_rows:
        file_path = output_dir / f"{sprint_name}_App23_{date_str}_{seq}.xlsx"
        best_app23 = max(app23_rows, key=lambda x: x.get("pass_rate", 0)) if app23_rows else None
        write_workbook(app23_rows, str(file_path), best_run=best_app23)
        print("✅ Created:", file_path)

    if config.get("claude", {}).get("enabled"):
        insight_text = generate_insights(sprint_rows)
        insight_file = Path(base_output_path).with_suffix(".insights.txt")
        insight_file.write_text(insight_text, encoding="utf-8")

    print(f"Workbook written to {base_output_path}")
    print(f"Runs matched before sprint filtering: {len(normalized_rows)}")
    print(f"Runs written for sprint window: {len(sprint_rows)}")


if __name__ == "__main__":
    main()