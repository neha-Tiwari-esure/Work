from __future__ import annotations

from collections import defaultdict
import re
from typing import Any, Dict, Iterable, List, Mapping

from client.analytics_api import AnalyticsApiClient

REASON_LABELS = {
    "unknown": "Not_Analysed",
    # "auto": "Automation_Issues",
    # TODO: Add env issues or product issues
}

CUSTOM_GROUP_RULES = [
    (
        "Owner assignment mismatch",
        [
            "feature owner",
            "claim file owner",
            "to match ' one of []' predicate",
            "to match ' one of [",
        ],
    ),
    (
        "Missing table column",
        [
            "was not found in the table",
            "actual columns:",
        ],
    ),
    (
        "Overlay blocked click",
        [
            "element click intercepted",
            "other element would receive the click",
            "rf-pp-shade",
        ],
    ),
    (
        "Queue/assignee mismatch",
        [
            "taskheaderform:assignedto",
            "queue name",
            "not assigned",
            "assignee",
            "teams queue",
        ],
    ),
]


def _split_csv_values(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, (list, tuple, set)):
        return [str(value).strip() for value in raw if str(value).strip()]
    return [value.strip() for value in str(raw).split(",") if value.strip()]


DETAIL_SEPARATOR = "\n\n---\n\n"


def _combine_unique_text(values: Iterable[Any], *, separator: str) -> str:
    seen: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.append(text)
    return separator.join(seen)


def _split_combined_blocks(raw: Any) -> list[str]:
    text = str(raw or "").strip()
    if not text:
        return []
    return [part.strip() for part in text.split(DETAIL_SEPARATOR) if part.strip()]


def _first_non_empty_line(*values: Any) -> str:
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        for line in text.splitlines():
            cleaned = line.strip()
            if cleaned:
                return cleaned
    return ""


def _normalize_message_key(message: Any, stack_trace: Any, test_name: Any) -> str:
    text = str(message or "").strip()
    if text:
        return text
    stack_line = _first_non_empty_line(stack_trace)
    if stack_line:
        return stack_line
    return str(test_name or "").strip()


def _clean_group_label(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(text or "").strip())
    cleaned = cleaned.replace("Expecting actual:", "Expectation mismatch:")
    cleaned = cleaned.replace("Checked that", "Check failed:")
    cleaned = cleaned.replace("Cannot invoke", "Null call:")
    cleaned = cleaned.replace("Index 0 out of bounds for length 0", "Index out of bounds")
    cleaned = cleaned.replace("java.lang.", "")
    return cleaned[:120] if cleaned else "Unclassified error"


def _build_group_name(message: Any, stack_trace: Any) -> str:
    message_text = str(message or "")
    stack_text = str(stack_trace or "")
    haystack = f"{message_text}\n{stack_text}".lower()

    for label, required_parts in CUSTOM_GROUP_RULES:
        if all(part in haystack for part in required_parts):
            return label
        if any(part in haystack for part in required_parts):
            return label

    exception_match = re.search(r"([A-Za-z0-9_$.]+(?:Exception|Error))", stack_text)
    first_line = _clean_group_label(_first_non_empty_line(message, stack_trace))
    if exception_match:
        exception_name = exception_match.group(1).split(".")[-1]
        if first_line and exception_name not in first_line:
            return f"{exception_name} — {first_line}"[:120]
        return exception_name[:120]
    return first_line


def dedupe_failure_details(grouped_rows: Mapping[str, Iterable[Mapping[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    deduped: Dict[str, List[Dict[str, Any]]] = {}

    for reason, rows in grouped_rows.items():
        buckets: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
        for row in rows:
            test_name = str(row.get("testName") or "").strip()
            buckets[test_name].append(row)

        deduped_rows: List[Dict[str, Any]] = []
        for _, bucket in buckets.items():
            first = dict(bucket[0])
            first.pop("testId", None)
            first["errorId"] = _combine_unique_text((item.get("errorId") for item in bucket), separator=", ")
            first["bugs"] = _combine_unique_text(
                (bug for item in bucket for bug in _split_csv_values(item.get("bugs"))),
                separator=", ",
            )
            first["testCaseId"] = _combine_unique_text(
                (case_id for item in bucket for case_id in _split_csv_values(item.get("testCaseId"))),
                separator=", ",
            )
            first["message"] = _combine_unique_text((item.get("message") for item in bucket), separator=DETAIL_SEPARATOR)
            first["stackTrace"] = _combine_unique_text((item.get("stackTrace") for item in bucket), separator=DETAIL_SEPARATOR)
            deduped_rows.append(first)

        deduped[reason] = deduped_rows

    return deduped


def group_failure_details_by_message(grouped_rows: Mapping[str, Iterable[Mapping[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped_output: Dict[str, List[Dict[str, Any]]] = {}

    for reason, rows in grouped_rows.items():
        buckets: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
        for row in rows:
            messages = _split_combined_blocks(row.get("message")) or [""]
            for message in messages:
                message_key = _normalize_message_key(message, row.get("stackTrace"), row.get("testName"))
                exploded_row = dict(row)
                exploded_row["message"] = message
                buckets[message_key].append(exploded_row)

        grouped_reason_rows: List[Dict[str, Any]] = []
        for message_key, bucket in buckets.items():
            first = bucket[0]
            grouped_reason_rows.append(
                {
                    "group_name": _build_group_name(first.get("message"), first.get("stackTrace")),
                    "failure_reason": reason,
                    "affected_test_count": len({str(item.get("testName") or "") for item in bucket if str(item.get("testName") or "").strip()}),
                    "testNames": _combine_unique_text((item.get("testName") for item in bucket), separator="\n"),
                    "testCaseIds": _combine_unique_text(
                        (case_id for item in bucket for case_id in _split_csv_values(item.get("testCaseId"))),
                        separator=", ",
                    ),
                    "runNames": _combine_unique_text((item.get("run_name") for item in bucket), separator=", "),
                    "products": _combine_unique_text((item.get("product") for item in bucket), separator=", "),
                    "bugs": _combine_unique_text(
                        (bug for item in bucket for bug in _split_csv_values(item.get("bugs"))),
                        separator=", ",
                    ),
                    "message": message_key,
                    "stackTraces": _combine_unique_text((item.get("stackTrace") for item in bucket), separator=DETAIL_SEPARATOR),
                }
            )

        grouped_reason_rows.sort(key=lambda row: (-int(row.get("affected_test_count") or 0), str(row.get("group_name") or "")))
        grouped_output[reason] = grouped_reason_rows

    return grouped_output


def collect_failure_details(
    client: AnalyticsApiClient,
    run_rows: Iterable[Mapping[str, Any]],
    reasons: Iterable[str],
) -> tuple[Dict[str, List[Dict[str, Any]]], Dict[str, Dict[str, int]]]:
    normalized_reasons = [reason.strip().lower() for reason in reasons if str(reason).strip()]
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    raw_reason_counts: Dict[str, int] = defaultdict(int)

    for run_row in run_rows:
        run_id = str(run_row.get("run_id") or "")
        run_name = str(run_row.get("run_name") or "")
        product = str(run_row.get("product") or "")
        batch_name = str(run_row.get("batch_name") or product or "")
        if not run_id:
            continue

        brief_rows = client.get_brief(run_id)
        for brief_row in brief_rows:
            failure_reason = str(brief_row.get("failureReason") or "").strip().lower()
            if failure_reason not in normalized_reasons:
                continue

            raw_reason_counts[failure_reason] += 1
            test_id = str(brief_row.get("id") or "")
            error_rows = client.get_test_errors(test_id) if test_id else []
            if not error_rows:
                grouped[failure_reason].append(
                    {
                        "run_id": run_id,
                        "run_name": run_name,
                        "product": product,
                        "batch_name": batch_name,
                        "failure_reason": failure_reason,
                        "testId": test_id,
                        "testName": brief_row.get("name"),
                        "testCaseId": ", ".join(str(value) for value in (brief_row.get("testCaseId") or [])),
                        "started": brief_row.get("started"),
                        "errorId": "",
                        "message": "",
                        "stackTrace": "",
                        "bugs": "",
                    }
                )
                continue

            for error_row in error_rows:
                grouped[failure_reason].append(
                    {
                        "run_id": run_id,
                        "run_name": run_name,
                        "product": product,
                        "batch_name": batch_name,
                        "failure_reason": failure_reason,
                        "testId": error_row.get("testId") or test_id,
                        "testName": brief_row.get("name"),
                        "testCaseId": ", ".join(str(value) for value in (brief_row.get("testCaseId") or [])),
                        "started": brief_row.get("started"),
                        "errorId": error_row.get("id") or "",
                        "message": error_row.get("message") or "",
                        "stackTrace": error_row.get("stackTrace") or "",
                        "bugs": ", ".join(str(value) for value in (error_row.get("bugs") or [])),
                    }
                )

    deduped = dedupe_failure_details(dict(grouped))
    summary_by_reason: Dict[str, Dict[str, int]] = {}
    for reason in normalized_reasons:
        rows = list(deduped.get(reason) or [])
        summary_by_reason[reason] = {
            "raw_failure_instances": int(raw_reason_counts.get(reason, 0)),
            "unique_test_names": len(rows),
        }

    return deduped, summary_by_reason
