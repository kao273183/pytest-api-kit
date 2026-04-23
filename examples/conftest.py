"""
Example conftest.py — copy this as your starting point.

It wires up:
- An APIClient fixture pointing at httpbin (swap for your real API)
- The pytest-html reporter extras (Endpoint/Status/Size/Payload/Description)
- A snapshot auto-save hook on pass + auto-diff hook on fail

All the moving parts live in the api_kit package; this file is intentionally
thin so you can see what's going on.
"""
import pytest
from pathlib import Path

from api_kit import APIClient, save_snapshot, compare_with_snapshot
from api_kit.reporters.html_extras import CLIENT_FIXTURES, install_html_extras


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def api_client():
    """HTTPBin is a free public API that echoes your request back — handy for
    learning the framework without needing your own server."""
    client = APIClient(base_url="https://httpbin.org")
    yield client
    client.session.close()


# ---------------------------------------------------------------------------
# Report & snapshot integration
# ---------------------------------------------------------------------------

# Tell the reporter which fixture names are APIClient instances so it can
# pull last_endpoint / last_status / etc. per test.
CLIENT_FIXTURES.extend(["api_client"])
install_html_extras()


SNAPSHOT_DIR = Path(__file__).parent / "data" / "api_snapshots"


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_runtest_makereport(item, call):
    """On pass: save/refresh snapshot. On fail: diff against baseline."""
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return

    # Find the APIClient used in this test
    client = None
    for name in CLIENT_FIXTURES:
        try:
            c = item.funcargs.get(name)
        except Exception:
            continue
        if c and getattr(c, "last_endpoint", ""):
            client = c
            break
    if not client:
        return

    endpoint = client.last_endpoint
    if report.passed:
        # Baseline fresh on every pass — sustainable because changes are small
        save_snapshot(
            endpoint=endpoint,
            status_code=client.last_status,
            data=client._last_response_data,
            size_bytes=client.last_size,
            snapshot_dir=SNAPSHOT_DIR,
        )
    elif report.failed:
        diff = compare_with_snapshot(
            endpoint=endpoint,
            status_code=client.last_status,
            data=client._last_response_data,
            size_bytes=client.last_size,
            snapshot_dir=SNAPSHOT_DIR,
        )
        if diff["status"] == "changed":
            report._api_diagnosis = "API_CHANGED: " + "; ".join(diff["changes"])
