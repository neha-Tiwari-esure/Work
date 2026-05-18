from __future__ import annotations
from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd
from openpyxl.styles import PatternFill


def write_workbook(rows: Iterable[Mapping], output_path: str, best_run=None) -> None:
    data = list(rows)
    df = pd.DataFrame(data)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        # ✅ Sheet 1 → Raw data
        df.to_excel(writer, sheet_name="Runs_Raw", index=False)

        # ✅ Highlight BEST RUN
        if not df.empty and best_run is not None:
            ws = writer.sheets["Runs_Raw"]

            green_fill = PatternFill(
                start_color="C6EFCE",
                end_color="C6EFCE",
                fill_type="solid"
            )

            best_idx = df["pass_rate"].idxmax()
            excel_row = best_idx + 2  # +1 header +1 index

            for col in range(1, ws.max_column + 1):
                ws.cell(row=excel_row, column=col).fill = green_fill

        # ✅ Sheet 2 → Summary (FIXED)
        if not df.empty:
            summary = pd.DataFrame(
                {
                    "metric": [
                        "run_count",
                        "total_tests",
                        "passed",
                        "failed",
                        "not_analysed",
                    ],
                    "value": [
                        len(df),
                        df["total_tests"].fillna(0).sum(),
                        df["passed"].fillna(0).sum(),
                        df["failed"].fillna(0).sum(),
                        df["not_analysed"].fillna(0).sum(),
                    ],
                }
            )

            summary.to_excel(writer, sheet_name="Sprint_Summary", index=False)