from __future__ import annotations

from typing import Iterable, Mapping


def build_summary_prompt(rows: Iterable[Mapping]) -> str:
    rows = list(rows)
    return (
        "You are summarizing EIS nightly regression results. "
        "Highlight run health, repeated failures, and notable changes.\n\n"
        f"Rows: {rows}"
    )


def generate_insights(rows: Iterable[Mapping]) -> str:
    # Placeholder only. Wire this to Claude once the data model is stable.
    rows = list(rows)
    if not rows:
        return "No runs found for the selected sprint window."
    return "Insights generation placeholder: connect Claude after API extraction is stable."
