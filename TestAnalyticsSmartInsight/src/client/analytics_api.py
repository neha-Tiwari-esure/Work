from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Union

import requests


@dataclass
class AnalyticsApiClient:
    base_url: str
    token: Optional[str] = None
    timeout_seconds: int = 30

    def __post_init__(self) -> None:
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        self.session.headers.update({"Accept": "application/json"})

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        response = self.session.get(url, params=params, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _repeatable_query(key: str, values: Union[str, Iterable[str]]) -> Dict[str, Any]:
        if isinstance(values, str):
            return {key: values}
        return {key: [value for value in values if value]}

    def get_batch_names(self, batch_ids: Union[str, Iterable[str]]) -> Dict[str, str]:
        payload = self.get("api/batches/names", params=self._repeatable_query("id", batch_ids))
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _flatten_batch_item(item: Dict[str, Any]) -> Dict[str, Any]:
        batch = item.get("batch") if isinstance(item.get("batch"), dict) else {}
        counts = item.get("counts") if isinstance(item.get("counts"), dict) else {}
        return {
            **batch,
            "counts": counts,
            "runsIDs": item.get("runsIDs") or [],
        }

    @staticmethod
    def _flatten_run_item(item: Dict[str, Any]) -> Dict[str, Any]:
        run = item.get("run") if isinstance(item.get("run"), dict) else {}
        counts = item.get("counts") if isinstance(item.get("counts"), dict) else {}
        return {
            **run,
            "counts": counts,
        }

    def get_batches(self, *, page_num: int = 1, page_size: int = 100) -> List[Dict[str, Any]]:
        payload = self.get(
            "api/batches",
            params={
                "page[num]": page_num,
                "page[size]": page_size,
            },
        )
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, list):
            return []
        return [self._flatten_batch_item(item) for item in data]

    def get_runs_for_batch(
        self,
        batch_id: str,
        *,
        include_improper_runs: bool = False,
        page_num: int = 1,
        page_size: int = 100000,
    ) -> List[Dict[str, Any]]:
        payload = self.get(
            "api/runs",
            params={
                "batchId": batch_id,
                "page[num]": page_num,
                "page[size]": page_size,
                "isProper": str(not include_improper_runs).lower(),
            },
        )
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, list):
            return []
        return [self._flatten_run_item(item) for item in data]

    def get_run(self, run_id: str) -> Dict[str, Any]:
        payload = self.get(f"api/runs/{run_id}")
        return payload if isinstance(payload, dict) else {}

    def get_aggregations(self, run_id: str) -> Dict[str, Any]:
        payload = self.get_run(run_id)
        aggregations = payload.get("aggregations") if isinstance(payload, dict) else None
        return aggregations if isinstance(aggregations, dict) else {}

    def get_brief(self, run_id: str) -> list[Dict[str, Any]]:
        payload = self.get(f"api/runs/{run_id}/brief")
        return payload if isinstance(payload, list) else []

    def get_bugs(self, run_id: str) -> list[Dict[str, Any]]:
        payload = self.get(f"api/runs/{run_id}/bugs")
        return payload if isinstance(payload, list) else []

    def get_run_history(self, run_id: str, page_num: int = 1, page_size: int = 100) -> Dict[str, Any]:
        payload = self.get(
            f"api/runs/{run_id}/history",
            params={"page[num]": page_num, "page[size]": page_size},
        )
        return payload if isinstance(payload, dict) else {}


def client_from_env(base_url: str) -> AnalyticsApiClient:
    return AnalyticsApiClient(
        base_url=base_url,
        token=os.getenv("TEST_ANALYTICS_TOKEN"),
    )
