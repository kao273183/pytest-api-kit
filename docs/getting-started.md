# Getting started — 30 minutes from empty repo to first CI run

## Prerequisites

- Python 3.9+
- An API you can reach from your machine (public or VPN-accessible)

## 1. New project (5 min)

```bash
mkdir my-api-tests && cd my-api-tests
python3 -m venv venv && source venv/bin/activate
pip install git+https://github.com/kao273183/pytest-api-kit.git pytest pytest-html
```

Copy the starter files from the kit:

```bash
# Adjust path to wherever you cloned the kit
KIT=~/Desktop/pytest-api-kit
cp $KIT/templates/conftest.py .
cp $KIT/templates/pytest.ini .
cp -r $KIT/templates/config .
cp $KIT/.gitignore .
mkdir -p tests data/api_snapshots
touch data/api_snapshots/.gitkeep
```

## 2. Configure (5 min)

Open `conftest.py`, change the `base_url` in the `api_client` fixture:

```python
@pytest.fixture(scope="session")
def api_client():
    client = APIClient(base_url="https://your-api.com")
    yield client
    client.session.close()
```

## 3. First test (10 min)

`tests/test_smoke.py`:

```python
import pytest
from api_kit import S, validate


class TestHealthcheck:
    """Reachability smoke — run these before anything else."""

    @pytest.mark.smoke
    def test_health(self, api_client):
        """GET /health — the only test that should ever fail for real bugs.

        Scenario: CI hits /health on deploy to confirm service is up.
        Asserts: 200 OK with {"status": "ok"}.
        Importance: Gates all downstream tests.
        """
        resp = api_client.get("/health")
        assert resp.status_code == 200
        validate(resp.json(), {"status": S.str})
```

Run:

```bash
pytest -v
open report.html
```

## 4. Adapt for auth (5 min)

Your API almost certainly needs auth. Pick the adapter that matches:

- **Bearer token** (API key or client credentials) → `docs/adapters/bearer-token.md`
- **OAuth with refresh** → `docs/adapters/oauth.md`
- **Multi-step (OTP / CAPTCHA / custom payload)** → `docs/adapters/otp-flow.md`

## 5. CI (5 min)

Drop this at `.github/workflows/smoke.yml`:

```yaml
name: smoke

on:
  push:
    branches: [main]
  schedule:
    - cron: '47 22 * * *'  # UTC — avoid :00/:30 peaks (GitHub drops those)

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e . pytest pytest-html
      - run: pytest -v
        env:
          API_PASSWORD: ${{ secrets.API_PASSWORD }}
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: report
          path: report.html
```

## Done — what next?

- **More than one API / service** → add more fixtures (each with its own `base_url`). See `api_kit.fixtures.make_client_fixture`.
- **Schema validation** → see `docs/schema-cookbook.md` for common response patterns.
- **Deploy to AWS Fargate** → see `pytest-api-kit-aws` (separate repo).
- **Self-service trigger panel for PMs** → see `pytest-api-kit-dashboard` (separate repo).
