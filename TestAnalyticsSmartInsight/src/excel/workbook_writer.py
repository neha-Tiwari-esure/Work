from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd


def write_workbook(rows: Iterable[Mapping], output_path: str) -> None:
    data = list(rows)
    df = pd.DataFrame(data)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Runs_Raw", index=False)

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
