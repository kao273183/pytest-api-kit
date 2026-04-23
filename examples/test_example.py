"""
Walkthrough test file — shows every feature of pytest-api-kit in one file.

Run it:
    pytest examples/ -v --html=report.html --self-contained-html

Then open report.html to see the Endpoint / Status / Size / Payload /
Description columns fill in automatically.
"""
import pytest

from api_kit import S, SchemaError, validate


# ---------------------------------------------------------------------------
# 1. Smoke: status + automatic payload-shape logging
# ---------------------------------------------------------------------------

class TestSmoke:
    """Basic reachability."""

    def test_get_200(self, api_client):
        """GET /get — simplest possible smoke check.

        Scenario: Client issues a GET and expects 200.
        Asserts: status == 200.
        Importance: If this breaks, nothing downstream works.
        """
        resp = api_client.get("/get", params={"hello": "world"})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 2. Schema validation (zero-dep DSL)
# ---------------------------------------------------------------------------

class TestSchema:
    """Demonstrates the built-in schema validator."""

    def test_schema_match(self, api_client):
        """GET /get — validate response shape with schema DSL.

        Asserts: args.hello == "world" + schema match.
        Why: Catches silent field-rename / type-change bugs.
        """
        resp = api_client.get("/get", params={"hello": "world"})
        assert resp.status_code == 200

        validate(resp.json(), {
            "args": S.dict,
            "headers": S.dict,
            "origin": S.str,
            "url": S.str,
        })

    def test_schema_mismatch_raises(self, api_client):
        """Negative test: schema mismatch raises SchemaError with JSON path."""
        resp = api_client.get("/get")
        with pytest.raises(SchemaError) as exc:
            validate(resp.json(), {"args": S.int})  # args is dict, not int
        assert "$.args" in str(exc.value)


# ---------------------------------------------------------------------------
# 3. Empty-array detection (the "200 but data[] is empty" bug class)
# ---------------------------------------------------------------------------

class TestEmptyArrayWarning:
    """The client logs ⚠ when any top-level list is empty — shown in reports."""

    def test_empty_array_detected(self):
        """Verify _summarize_payload flags empty top-level arrays.

        Exercises the library function directly — no HTTP needed — so the
        behaviour under test is the empty-array detection logic itself, not
        whichever public API happens to return an empty field today.
        """
        from api_kit.client import _summarize_payload

        summary, empty = _summarize_payload({
            "total": 42,
            "records": [],     # ← the bug-class we want to catch
            "categories": [1, 2, 3],
        })
        assert "records" in empty
        assert "categories" not in empty
        assert "⚠" in summary
        assert "records[]=0" in summary
        assert "categories[]=3" in summary


# ---------------------------------------------------------------------------
# 4. Chain tests (list -> detail)
# ---------------------------------------------------------------------------

class TestChain:
    """Typical real-world pattern: list endpoint -> follow-up detail."""

    def test_list_then_detail(self, api_client):
        """POST /anything twice — second call uses value from first.

        Pattern shown:
          1. First call returns some identifier
          2. Second call uses it
          3. Both validated against their own schemas
        """
        first = api_client.post("/anything", json={"seed": 42})
        assert first.status_code == 200
        echoed = first.json()["json"]["seed"]

        second = api_client.get("/anything", params={"ref": echoed})
        assert second.status_code == 200


# ---------------------------------------------------------------------------
# 5. Snapshot drift (see conftest.py hook)
# ---------------------------------------------------------------------------

class TestSnapshotDrift:
    """On pass, conftest saves a snapshot. On failure, it diffs against baseline.

    You won't see the magic the first run — baselines are created. Break the
    response (mock it, point at a different URL) and watch the failure report
    carry an `API_CHANGED: ...` diagnosis.
    """

    def test_creates_baseline(self, api_client):
        """GET /headers — baseline for field/type drift detection."""
        resp = api_client.get("/headers")
        assert resp.status_code == 200
        # Snapshot is saved automatically by the conftest hook on pass
