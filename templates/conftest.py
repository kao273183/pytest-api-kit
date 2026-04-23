"""
Starter conftest.py for a new project.

Copy this as your project root's conftest.py and edit:
1. `base_url` — point at your API
2. (Optional) `extra_headers` — WAF bypass, tenant ID, etc.
3. (Optional) auth — see docs/adapters/ for Bearer / OAuth / OTP examples
"""
import pytest
from pathlib import Path

from api_kit import APIClient, save_snapshot, compare_with_snapshot
from api_kit.reporters.html_extras import CLIENT_FIXTURES, install_html_extras


# ---------------------------------------------------------------------------
# Fixtures — adjust for your API
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def api_client():
    client = APIClient(
        base_url="https://api.example.com",
        # extra_headers={"X-Tenant-ID": "acme"},
    )
    yield client
    client.session.close()


# ---------------------------------------------------------------------------
# Report + snapshot integration
# ---------------------------------------------------------------------------

CLIENT_FIXTURES.extend(["api_client"])  # add every fixture name you use above
install_html_extras()

SNAPSHOT_DIR = Path(__file__).parent / "data" / "api_snapshots"


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return

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
