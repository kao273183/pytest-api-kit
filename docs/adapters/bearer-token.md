# Adapter: Bearer token (API key / static token)

Simplest auth case — you have one long-lived token (API key, personal access
token, or service account token) and every request carries it.

## Setup

`conftest.py`:

```python
import os
import pytest
from api_kit import APIClient
from api_kit.reporters.html_extras import CLIENT_FIXTURES, install_html_extras


@pytest.fixture(scope="session")
def api_client():
    token = os.environ["API_TOKEN"]  # fail loud if missing
    client = APIClient(base_url="https://api.example.com", token=token)
    yield client
    client.session.close()


CLIENT_FIXTURES.extend(["api_client"])
install_html_extras()
```

## Run

```bash
export API_TOKEN=xxx
pytest -v
```

## In CI

GitHub Actions:

```yaml
- run: pytest -v
  env:
    API_TOKEN: ${{ secrets.API_TOKEN }}
```

## Gotchas

### Don't put the token in `env.yaml`

It's too easy to commit by accident. Use env vars (for CI) or a secret manager
(for local dev — macOS Keychain, `pass`, 1Password CLI).

### If your header is not `Authorization: Bearer`

Some APIs use `X-API-Key` or similar:

```python
client = APIClient(
    base_url="https://api.example.com",
    extra_headers={"X-API-Key": os.environ["API_KEY"]},
)
```

### Token expires mid-run

For short-lived tokens, use the OAuth adapter instead — it shows how to wrap a
refresh function so `api_client` transparently renews.
