#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def walk_items(items: list[dict[str, Any]], prefix: str = "") -> None:
    for item in items:
        name = item.get("name", "<unnamed>")
        request = item.get("request")
        if request:
            method = request.get("method", "?")
            url = request.get("url")
            if isinstance(url, dict):
                raw = url.get("raw") or ""
            else:
                raw = str(url or "")
            print(f"REQUEST {prefix}{name} | {method} | {raw}")
        else:
            print(f"FOLDER  {prefix}{name}")
            walk_items(item.get("item", []), prefix=f"{prefix}{name} / ")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/inspect_postman_export.py <collection.json>")
        raise SystemExit(1)

    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    print("Collection:", data.get("info", {}).get("name", path.name))
    walk_items(data.get("item", []))


if __name__ == "__main__":
    main()
