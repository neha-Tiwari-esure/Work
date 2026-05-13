from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional


def looks_like_nightly(*texts: str, patterns: list[str]) -> bool:
    haystack = " ".join(text for text in texts if text).lower()
    return any(pattern.lower() in haystack for pattern in patterns)


def matches_exact_run_names(run_name: str, exact_names: list[str]) -> bool:
    if not exact_names:
        return True
    normalized = run_name.strip().lower()
    return any(normalized == name.strip().lower() for name in exact_names if name.strip())


def extract_run_data(run_payload: Mapping[str, Any]) -> Dict[str, Any]:
    if "run" in run_payload and isinstance(run_payload.get("run"), dict):
        return dict(run_payload["run"])
    return {
        key: value
        for key, value in run_payload.items()
        if key not in {"counts", "aggregations", "brief", "bugs", "attachments", "history"}
    }


def _flatten_search_values(value: Any) -> Iterator[str]:
    if value is None:
        return
    if isinstance(value, str):
        if value.strip():
            yield value
        return
    if isinstance(value, Mapping):
        for key, nested in value.items():
            yield from _flatten_search_values(key)
            yield from _flatten_search_values(nested)
        return
    if isinstance(value, (list, tuple, set)):
        for nested in value:
            yield from _flatten_search_values(nested)
        return
    yield str(value)


def derive_product_label(
    filters: list[str],
    run_summary: Mapping[str, Any],
    run_payload: Mapping[str, Any],
    batch_name: str = "",
) -> str:
    if not filters:
        return batch_name or str(run_summary.get("name") or extract_run_data(run_payload).get("name") or "")

    run_data = extract_run_data(run_payload)
    searchable = " | ".join(
        value.lower()
        for value in _flatten_search_values(
            [
                batch_name,
                run_summary.get("name"),
                run_summary.get("tags"),
                run_summary.get("properties"),
                run_data.get("name"),
                run_data.get("batchName"),
                run_data.get("tags"),
                run_data.get("properties"),
            ]
        )
    )

    for product_filter in filters:
        if product_filter.lower() in searchable:
            return product_filter

    return ""


def matches_product_filters(
    filters: list[str],
    run_summary: Mapping[str, Any],
    run_payload: Mapping[str, Any],
    batch_name: str = "",
) -> bool:
    if not filters:
        return True
    return bool(derive_product_label(filters, run_summary, run_payload, batch_name=batch_name))


def normalize_run_record(
    product: str,
    run_payload: Dict[str, Any],
    brief_payload: Optional[List[Dict[str, Any]]] = None,
    bugs_payload: Optional[List[Dict[str, Any]]] = None,
    batch_name: str = "",
    batch_id: str = "",
) -> Dict[str, Any]:
    run_data = extract_run_data(run_payload)
    counts = run_payload.get("counts") if isinstance(run_payload.get("counts"), dict) else {}
    aggregations = run_payload.get("aggregations") if isinstance(run_payload.get("aggregations"), dict) else {}
    statuses = counts.get("statuses") if isinstance(counts.get("statuses"), dict) else {}
    reasons = counts.get("reasons") if isinstance(counts.get("reasons"), dict) else {}
    brief_payload = brief_payload or []
    bugs_payload = bugs_payload or []

    return {
        "product": product,
        # "batch_id": run_data.get("batchId") or batch_id,
        # "batch_name": run_data.get("batchName") or batch_name,
        # "run_id": run_data.get("id") or run_data.get("runId"),
        "run_name": run_data.get("name") or run_data.get("runName"),
        "run_status": run_data.get("status"),
        "execution_datetime": run_data.get("started") or run_data.get("dateTime") or run_data.get("executedAt"),
        "finished_datetime": run_data.get("finished"),
        "duration": run_data.get("effectiveDuration") or run_data.get("duration"),
        # "is_proper": run_data.get("isProper"),
        "merge_count": run_data.get("mergeCount"),
        "total_tests": counts.get("total"),
        "incomplete": counts.get("incomplete"),
        "pass_rate": counts.get("passRate"),
        "analysis_ratio": counts.get("analysisRatio"),
        "passed": statuses.get("passed"),
        "failed": statuses.get("failed"),
        "skipped": statuses.get("skipped"),
        "not_analysed": reasons.get("unknown"),
        "in_analysis": reasons.get("in_analysis"),
        "automation_issues": reasons.get("auto"),
        "performance_issues": reasons.get("perf"),
        "product_issues": reasons.get("prod"),
        "environment_issues": reasons.get("env"),
        # "total_methods": aggregations.get("totalMethods"),
        # "active_methods": aggregations.get("activeMethods"),
        # "active_tests": aggregations.get("activeTests"),
        # "total_methods_plain_duration": aggregations.get("totalMethodsPlainDuration"),
        # "active_methods_plain_duration": aggregations.get("activeMethodsPlainDuration"),
        # "active_tests_plain_duration": aggregations.get("activeTestsPlainDuration"),
        # "total_methods_effective_duration": aggregations.get("totalMethodsEffectiveDuration"),
        # "active_methods_effective_duration": aggregations.get("activeMethodsEffectiveDuration"),
        # "active_tests_effective_duration": aggregations.get("activeTestsEffectiveDuration"),
        "brief_rows": len(brief_payload),
        "bug_count": len(bugs_payload),
        "tags": ", ".join(str(tag) for tag in (run_data.get("tags") or [])),
    }


def filter_runs_for_sprint(rows: Iterable[Dict[str, Any]], sprint_start: str, sprint_end: str) -> List[Dict[str, Any]]:
    start = datetime.fromisoformat(sprint_start)
    end = datetime.fromisoformat(sprint_end)
    result: List[Dict[str, Any]] = []
    for row in rows:
        raw = row.get("execution_datetime")
        if not raw:
            continue
        try:
            dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except ValueError:
            continue
        if start <= dt.replace(tzinfo=None) <= end:
            result.append(row)
    return result
