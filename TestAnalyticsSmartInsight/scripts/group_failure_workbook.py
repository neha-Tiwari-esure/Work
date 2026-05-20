from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from analysis.failure_analyzer import REASON_LABELS, group_failure_details_by_message  # noqa: E402


def build_output_path(input_path: Path, output_path: str | None) -> Path:
    if output_path:
        return Path(output_path)
    return input_path.with_name(f"{input_path.stem}_GroupedByMessage{input_path.suffix}")


def load_reason_sheets(input_path: Path) -> dict[str, list[dict]]:
    inverse_labels = {label: reason for reason, label in REASON_LABELS.items()}
    workbook = pd.ExcelFile(input_path)
    grouped_rows: dict[str, list[dict]] = {}

    for sheet_name in workbook.sheet_names:
        reason = inverse_labels.get(sheet_name)
        if not reason:
            continue
        df = pd.read_excel(input_path, sheet_name=sheet_name).fillna("")
        grouped_rows[reason] = df.to_dict(orient="records")

    return grouped_rows


def write_grouped_workbook(grouped_message_rows: dict[str, list[dict]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ordered_reasons = [reason for reason in ("unknown", "auto") if grouped_message_rows.get(reason)]
    ordered_reasons.extend(reason for reason in grouped_message_rows if reason not in ordered_reasons and grouped_message_rows.get(reason))

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        summary_rows = []

        for reason in ordered_reasons:
            rows = list(grouped_message_rows.get(reason) or [])
            if not rows:
                continue

            df = pd.DataFrame(rows)
            sheet_name = f"{REASON_LABELS.get(reason, reason.title())}_Groups"[:31]
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            summary_rows.append(
                {
                    "failure_reason": reason,
                    "message_groups": len(df),
                    "affected_tests_total": int(df["affected_test_count"].fillna(0).sum()) if "affected_test_count" in df else 0,
                }
            )

        if summary_rows:
            pd.DataFrame(summary_rows).to_excel(writer, sheet_name="Summary", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Group a filtered failure-analysis workbook by shared error message.")
    parser.add_argument("input_workbook", help="Path to the filtered failure-analysis workbook created by src/main.py")
    parser.add_argument("--output", help="Optional output workbook path override")
    args = parser.parse_args()

    input_path = Path(args.input_workbook)
    if not input_path.exists():
        raise SystemExit(f"Input workbook not found: {input_path}")

    grouped_rows = load_reason_sheets(input_path)
    if not grouped_rows:
        raise SystemExit("No failure-analysis sheets were found in the input workbook.")

    grouped_message_rows = group_failure_details_by_message(grouped_rows)
    output_path = build_output_path(input_path, args.output)
    write_grouped_workbook(grouped_message_rows, output_path)
    print(f"✅ Created grouped workbook: {output_path}")


if __name__ == "__main__":
    main()
