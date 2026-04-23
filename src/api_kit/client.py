"""
APIClient — HTTP client with built-in observability.

Every call auto-logs:
- method + URL
- status + size + duration
- payload shape summary (top-level keys + list counts)
- empty-array warnings (catches "200 but data[] is empty" bugs)

Also caches last response JSON for downstream snapshot diffing.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)


def _summarize_payload(data: Any, max_keys: int = 8) -> Tuple[str, List[str]]:
    """Produce a one-line shape summary plus list of empty-array fields.

    The summary tags each top-level key so a 200-but-empty response is obvious
    in the log:
        total=42  items[]=15  errors[]=0⚠
    The second return value lists keys whose value is an empty list — the
    caller can decide whether to log a warning, fail the test, etc.
    """
    if data is None:
        return "null", []
    if isinstance(data, list):
        return (
            f"[list × {len(data)}]" + ("  ⚠empty" if not data else ""),
            ([] if data else ["<root>"]),
        )
    if not isinstance(data, dict):
        return f"({type(data).__name__})", []

    parts: List[str] = []
    empty: List[str] = []
    for k, v in list(data.items())[:max_keys]:
        if isinstance(v, list):
            tag = f"{k}[]={len(v)}"
            if not v:
                tag += "⚠"
                empty.append(k)
            parts.append(tag)
        elif v is None:
            parts.append(f"{k}=null")
        elif isinstance(v, bool):
            parts.append(f"{k}={str(v).lower()}")
        elif isinstance(v, (int, float)):
            parts.append(f"{k}={v}")
        elif isinstance(v, str):
            val = v if len(v) <= 20 else v[:17] + "…"
            parts.append(f'{k}="{val}"')
        elif isinstance(v, dict):
            parts.append(f"{k}={{{len(v)}k}}")
    if len(data) > max_keys:
        parts.append(f"+{len(data) - max_keys}…")
    return "  ".join(parts), empty


class APIClient:
    """Minimal wrapper around requests.Session with observability hooks.

    Args:
        base_url: API root. Each call's endpoint is appended to this.
        token: Optional Bearer token. Use set_token() to change later.
        extra_headers: Extra headers applied to every request (e.g. WAF bypass).
        timeout: Default request timeout in seconds.
        user_agent: Identifier for server-side logging.

    Attributes (reset on each request):
        last_endpoint, last_status, last_duration_ms, last_size,
        last_payload_summary, last_empty_fields
    """

    def __init__(
        self,
        base_url: str,
        token: str = "",
        extra_headers: Optional[Dict[str, str]] = None,
        timeout: float = 15.0,
        user_agent: str = "pytest-api-kit/1.0",
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": user_agent,
        })
        if extra_headers:
            self.session.headers.update(extra_headers)
        if token:
            self.set_token(token)

        # Response tracking (used by pytest-html reporter hooks)
        self.last_endpoint = ""
        self.last_status = 0
        self.last_duration_ms = 0.0
        self.last_size = 0
        self.last_payload_summary = ""
        self.last_empty_fields: List[str] = []
        self._last_response_data: Any = None

    def set_token(self, token: str) -> None:
        """Set Authorization: Bearer header."""
        self.session.headers["Authorization"] = f"Bearer {token}"

    def set_header(self, name: str, value: str) -> None:
        """Set an arbitrary header (persists across requests)."""
        self.session.headers[name] = value

    def request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        timeout = kwargs.pop("timeout", self.timeout)
        logger.info(f"{method} {url}")

        start = time.perf_counter()
        response = self.session.request(method, url, timeout=timeout, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000

        self.last_endpoint = f"{method} {endpoint}"
        self.last_status = response.status_code
        self.last_duration_ms = round(elapsed_ms, 1)
        self.last_size = len(response.content)

        try:
            self._last_response_data = response.json()
        except (ValueError, TypeError):
            self._last_response_data = None

        summary, empty_fields = _summarize_payload(self._last_response_data)
        self.last_payload_summary = summary
        self.last_empty_fields = empty_fields

        logger.info(
            f"  -> {response.status_code} ({self.last_size} bytes, {self.last_duration_ms}ms)"
        )
        if summary:
            logger.info(f"     payload: {summary}")
        if empty_fields:
            logger.warning(f"     ⚠ empty fields: {', '.join(empty_fields)}")
        if response.status_code >= 400:
            logger.debug(f"  resp headers: {dict(response.headers)}")
            logger.debug(f"  req headers: {dict(response.request.headers)}")
        return response

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> requests.Response:
        return self.request("GET", endpoint, params=params, **kwargs)

    def post(self, endpoint: str, json: Optional[Dict[str, Any]] = None, **kwargs) -> requests.Response:
        return self.request("POST", endpoint, json=json, **kwargs)

    def put(self, endpoint: str, json: Optional[Dict[str, Any]] = None, **kwargs) -> requests.Response:
        return self.request("PUT", endpoint, json=json, **kwargs)

    def patch(self, endpoint: str, json: Optional[Dict[str, Any]] = None, **kwargs) -> requests.Response:
        return self.request("PATCH", endpoint, json=json, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("DELETE", endpoint, **kwargs)
