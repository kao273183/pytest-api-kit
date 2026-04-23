"""
API response snapshot & drift detection.

Stores a per-endpoint baseline (field paths + types + response size) so future
runs can detect:
- Added / removed fields
- Type changes (str -> int, etc.)
- Response size drift (±30% AND ±2KB, whichever is larger)

Usage in conftest.py:
    from api_kit.snapshot import save_snapshot, compare_with_snapshot

    # On pass: save baseline (once enough)
    save_snapshot(endpoint="GET /api/users", status_code=200,
                  data=response.json(), size_bytes=len(response.content),
                  snapshot_dir=Path("data/api_snapshots"))

    # On fail: diff against baseline to classify the failure
    diff = compare_with_snapshot(endpoint="GET /api/users",
                                 status_code=500, data={}, size_bytes=0,
                                 snapshot_dir=Path("data/api_snapshots"))
    # diff["status"] ∈ {"unchanged", "changed", "no_snapshot"}
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# Drift thresholds
SIZE_DRIFT_RATIO = 0.30          # ±30% swing
SIZE_DRIFT_FLOOR_BYTES = 2048    # …or ±2 KB, whichever is larger


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return type(value).__name__


def capture_schema(data: Any, prefix: str = "$") -> List[str]:
    """Extract field paths with types from response data, returned sorted.

    Example output:
        ["$.items:list",
         "$.items[].id:str",
         "$.items[].title:str",
         "$.total:int"]
    """
    paths = []

    if isinstance(data, dict):
        for key, value in data.items():
            path = f"{prefix}.{key}"
            paths.append(f"{path}:{_type_name(value)}")
            if isinstance(value, dict):
                paths.extend(capture_schema(value, path))
            elif isinstance(value, list) and value:
                item = value[0]
                paths.append(f"{path}[]:{_type_name(item)}")
                if isinstance(item, dict):
                    paths.extend(capture_schema(item, f"{path}[]"))
    elif isinstance(data, list) and data:
        item = data[0]
        paths.append(f"{prefix}[]:{_type_name(item)}")
        if isinstance(item, dict):
            paths.extend(capture_schema(item, f"{prefix}[]"))

    return sorted(set(paths))


def _endpoint_to_filename(endpoint: str) -> str:
    """Convert 'GET /api/v1/users' -> 'GET_api_v1_users.json'."""
    safe = re.sub(r"[^a-zA-Z0-9]", "_", endpoint)
    safe = re.sub(r"_+", "_", safe).strip("_")
    return f"{safe}.json"


def save_snapshot(
    endpoint: str,
    status_code: int,
    data: Any,
    size_bytes: Optional[int] = None,
    snapshot_dir: Path = Path("data/api_snapshots"),
) -> Path:
    """Save API response schema as snapshot baseline."""
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    field_paths = capture_schema(data)

    schema = {}
    if isinstance(data, dict):
        schema = {k: _type_name(v) for k, v in data.items()}

    snapshot = {
        "endpoint": endpoint,
        "status_code": status_code,
        "schema": schema,
        "field_paths": field_paths,
        "captured_at": datetime.now().isoformat(timespec="seconds"),
    }
    if size_bytes is not None:
        snapshot["size_bytes"] = int(size_bytes)

    filepath = snapshot_dir / _endpoint_to_filename(endpoint)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    return filepath


def load_snapshot(
    endpoint: str,
    snapshot_dir: Path = Path("data/api_snapshots"),
) -> Optional[Dict]:
    filepath = snapshot_dir / _endpoint_to_filename(endpoint)
    if not filepath.exists():
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def _size_drift(old_size: Optional[int], new_size: Optional[int]) -> Optional[str]:
    """Return a human-readable drift message if significant, else None.

    Flagged when exceeds BOTH the ratio threshold AND the byte floor — prevents
    tiny swings (40B -> 60B) from being noisy while still catching huge
    percentage moves on small payloads.
    """
    if old_size is None or new_size is None:
        return None
    if old_size == 0 and new_size == 0:
        return None
    diff = new_size - old_size
    abs_diff = abs(diff)
    if abs_diff < SIZE_DRIFT_FLOOR_BYTES:
        return None
    if old_size > 0 and abs_diff / old_size < SIZE_DRIFT_RATIO:
        return None
    sign = "+" if diff > 0 else ""
    pct = f"{(diff / old_size * 100):+.0f}%" if old_size else "N/A"
    return f"Response size: {old_size}B -> {new_size}B ({sign}{diff}B, {pct})"


def compare_with_snapshot(
    endpoint: str,
    status_code: int,
    data: Any,
    size_bytes: Optional[int] = None,
    snapshot_dir: Path = Path("data/api_snapshots"),
) -> Dict:
    """Compare current response with baseline. Returns a dict with:
        status:         "unchanged" | "changed" | "no_snapshot"
        changes:        list[str]  human-readable change descriptions
        added_fields:   list[str]
        removed_fields: list[str]
        type_changes:   list[str]
        status_code_changed: bool
        size_changed:   bool
        size_delta:     str | None
    """
    old = load_snapshot(endpoint, snapshot_dir)
    if old is None:
        return {"status": "no_snapshot", "changes": ["No baseline snapshot found"]}

    current_paths = set(capture_schema(data))
    old_paths = set(old.get("field_paths", []))

    def _parse_paths(paths):
        result = {}
        for p in paths:
            if ":" in p:
                path, typ = p.rsplit(":", 1)
                result[path] = typ
        return result

    current_map = _parse_paths(current_paths)
    old_map = _parse_paths(old_paths)

    current_keys = set(current_map.keys())
    old_keys = set(old_map.keys())

    added = current_keys - old_keys
    removed = old_keys - current_keys
    common = current_keys & old_keys

    type_changes = []
    for key in common:
        if current_map[key] != old_map[key]:
            type_changes.append(f"{key}: {old_map[key]} -> {current_map[key]}")

    status_changed = old.get("status_code") != status_code
    size_msg = _size_drift(old.get("size_bytes"), size_bytes)

    changes = []
    if status_changed:
        changes.append(f"Status code: {old.get('status_code')} -> {status_code}")
    if added:
        changes.append(f"New fields: {', '.join(sorted(added))}")
    if removed:
        changes.append(f"Removed fields: {', '.join(sorted(removed))}")
    if type_changes:
        changes.append(f"Type changes: {'; '.join(type_changes)}")
    if size_msg:
        changes.append(size_msg)

    return {
        "status": "changed" if changes else "unchanged",
        "changes": changes,
        "added_fields": sorted(added),
        "removed_fields": sorted(removed),
        "type_changes": type_changes,
        "status_code_changed": status_changed,
        "size_changed": size_msg is not None,
        "size_delta": size_msg,
    }
