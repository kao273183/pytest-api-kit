"""
pytest-html 4.x report extras.

Adds columns to the test results table:
    Endpoint | Status | API Time | Size | Payload | Diagnosis | Description

Hook into your conftest.py like this:

    # conftest.py
    from api_kit.reporters.html_extras import (
        install_html_extras,
        CLIENT_FIXTURES,
    )

    # Tell the reporter which fixture names are APIClient instances
    CLIENT_FIXTURES.extend(["api_client", "auth_client"])

    install_html_extras()  # registers pytest_html_* hooks via globals()


Each test's docstring becomes the Description cell:
  - First line shown (truncated to ~60 chars)
  - Full docstring as tooltip via `title` attribute
"""
from __future__ import annotations

from typing import List

import pytest

# User fills this list in their conftest.py with the fixture names they use.
CLIENT_FIXTURES: List[str] = []


def install_html_extras():
    """Monkey-patch the calling module's namespace with pytest-html hooks.

    Called from conftest.py — the hooks must live at module scope for pytest
    to discover them. We inject them into the caller's globals().
    """
    import inspect

    caller = inspect.currentframe().f_back
    g = caller.f_globals

    g["pytest_html_report_title"] = _pytest_html_report_title
    g["pytest_html_results_table_header"] = _pytest_html_results_table_header
    g["pytest_runtest_makereport"] = _pytest_runtest_makereport
    g["pytest_html_results_table_row"] = _pytest_html_results_table_row


def _pytest_html_report_title(report):
    report.title = "API Test Report"


def _pytest_html_results_table_header(cells):
    cells.insert(3, '<th class="sortable" data-column-type="text">Endpoint</th>')
    cells.insert(4, '<th class="sortable" data-column-type="numeric">Status</th>')
    cells.insert(5, '<th class="sortable" data-column-type="numeric">API Time</th>')
    cells.insert(6, '<th data-column-type="text">Size</th>')
    cells.insert(7, '<th data-column-type="text">Payload</th>')
    cells.insert(8, '<th data-column-type="text">Description</th>')


@pytest.hookimpl(hookwrapper=True)
def _pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return

    endpoint = ""
    status = 0
    duration = 0.0
    size = 0
    payload_summary = ""
    empty_fields: List[str] = []

    for name in CLIENT_FIXTURES:
        if name not in item.fixturenames:
            continue
        try:
            client = item.funcargs.get(name)
        except Exception:
            continue
        if client and getattr(client, "last_endpoint", ""):
            endpoint = client.last_endpoint
            status = client.last_status
            duration = client.last_duration_ms
            size = client.last_size
            payload_summary = getattr(client, "last_payload_summary", "")
            empty_fields = list(getattr(client, "last_empty_fields", []) or [])
            break

    report._api_endpoint = endpoint
    report._api_status = status
    report._api_duration = duration
    report._api_size = size
    report._api_payload_summary = payload_summary
    report._api_empty_fields = empty_fields

    doc = (getattr(item.function, "__doc__", "") or "").strip()
    report._api_doc_full = doc
    report._api_doc_summary = doc.splitlines()[0].strip() if doc else ""


def _pytest_html_results_table_row(report, cells):
    endpoint = getattr(report, "_api_endpoint", "")
    status = getattr(report, "_api_status", 0)
    duration = getattr(report, "_api_duration", 0)
    size = getattr(report, "_api_size", 0)

    # Endpoint
    ep_html = (
        f'<td class="col-endpoint">{endpoint}</td>'
        if endpoint
        else '<td class="col-endpoint" style="color:#c0c5d0">-</td>'
    )

    # Status (coloured by 2xx/4xx/5xx)
    if status:
        if 200 <= status < 300:
            color = "#059669"
        elif 400 <= status < 500:
            color = "#d97706"
        elif status >= 500:
            color = "#dc2626"
        else:
            color = "inherit"
        st_html = f'<td class="col-status" style="color:{color}">{status}</td>'
    else:
        st_html = '<td class="col-status" style="color:#c0c5d0">-</td>'

    # API Time (coloured by threshold)
    if duration:
        if duration < 300:
            dur_color = "#059669"
        elif duration < 800:
            dur_color = "#d97706"
        else:
            dur_color = "#dc2626"
        dur_html = f'<td class="col-apiTime" style="color:{dur_color}">{duration}ms</td>'
    else:
        dur_html = '<td class="col-apiTime" style="color:#c0c5d0">-</td>'

    # Size
    if size:
        size_str = f"{size / 1024:.1f}KB" if size > 1024 else f"{size}B"
        sz_html = f'<td class="col-size">{size_str}</td>'
    else:
        sz_html = '<td class="col-size" style="color:#c0c5d0">-</td>'

    # Payload shape
    payload_summary = getattr(report, "_api_payload_summary", "")
    empty_fields = getattr(report, "_api_empty_fields", []) or []
    if payload_summary:
        title = payload_summary.replace('"', "&quot;")
        display = payload_summary if len(payload_summary) <= 48 else payload_summary[:45] + "…"
        color = "#d97706" if empty_fields else "#475569"
        tag = "⚠ " if empty_fields else ""
        pl_html = (
            f'<td class="col-payload" style="color:{color};font-size:0.78em;'
            f'font-family:ui-monospace,Menlo,monospace;white-space:nowrap;" '
            f'title="{title}">{tag}{display}</td>'
        )
    else:
        pl_html = '<td class="col-payload" style="color:#c0c5d0">-</td>'

    # Description (docstring first line + full as tooltip)
    doc_summary = getattr(report, "_api_doc_summary", "")
    doc_full = getattr(report, "_api_doc_full", "")
    if doc_summary:
        title = doc_full.replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
        display = doc_summary if len(doc_summary) <= 60 else doc_summary[:57] + "…"
        desc_html = (
            f'<td class="col-desc" style="color:#334155;font-size:0.85em;'
            f'max-width:380px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" '
            f'title="{title}">{display}</td>'
        )
    else:
        desc_html = '<td class="col-desc" style="color:#c0c5d0">-</td>'

    cells.insert(3, ep_html)
    cells.insert(4, st_html)
    cells.insert(5, dur_html)
    cells.insert(6, sz_html)
    cells.insert(7, pl_html)
    cells.insert(8, desc_html)
