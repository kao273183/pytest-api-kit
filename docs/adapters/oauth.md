# Adapter: OAuth with refresh

Short-lived access token + refresh token. You need to:
1. Fetch a fresh access token at start-of-session
2. Transparently refresh when it expires mid-run

## Minimal TokenManager

`utils/auth.py` (user-owned code, in your project):

```python
import os
import time
import requests


class TokenManager:
    """Handles client-credentials OAuth2 with refresh."""

    TOKEN_URL = "https://auth.example.com/oauth/token"

    def __init__(self):
        self._token = ""
        self._expires_at = 0

    def get_token(self) -> str:
        """Return a valid token, refreshing if expired."""
        if self._token and time.time() < self._expires_at - 30:  # 30s safety
            return self._token

        resp = requests.post(self.TOKEN_URL, data={
            "grant_type": "client_credentials",
            "client_id": os.environ["OAUTH_CLIENT_ID"],
            "client_secret": os.environ["OAUTH_CLIENT_SECRET"],
        }, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        self._token = data["access_token"]
        self._expires_at = time.time() + data.get("expires_in", 3600)
        return self._token

    @property
    def is_expired(self) -> bool:
        return time.time() >= self._expires_at - 30
```

## Wire into conftest.py

```python
import pytest
from api_kit import APIClient
from api_kit.reporters.html_extras import CLIENT_FIXTURES, install_html_extras
from .utils.auth import TokenManager


@pytest.fixture(scope="session")
def token_manager():
    return TokenManager()


@pytest.fixture(scope="session")
def api_client(token_manager):
    client = APIClient(base_url="https://api.example.com")
    client.set_token(token_manager.get_token())
    # Stash manager on client for auto-refresh hook below
    client._token_manager = token_manager
    yield client
    client.session.close()


@pytest.fixture(autouse=True)
def _auto_refresh_token(request):
    """Refresh token before any test using a client with one attached."""
    for name in ("api_client",):
        if name not in request.fixturenames:
            continue
        client = request.getfixturevalue(name)
        mgr = getattr(client, "_token_manager", None)
        if mgr and mgr.is_expired:
            client.set_token(mgr.get_token())


CLIENT_FIXTURES.extend(["api_client"])
install_html_extras()
```

## Why autouse for refresh?

pytest fixtures with `scope="session"` are created once. Without the `autouse`
hook, a multi-hour test run would hit auth failures when the token expires.
The hook adds <1ms per test and only actually calls the refresh endpoint when
needed.

## Multiple clients sharing one TokenManager

If your system has multiple services on the same OAuth realm, share one
`token_manager` fixture across all clients:

```python
@pytest.fixture(scope="session")
def members_client(token_manager):
    client = APIClient(base_url="https://members.example.com")
    client.set_token(token_manager.get_token())
    client._token_manager = token_manager
    yield client


@pytest.fixture(scope="session")
def billing_client(token_manager):
    client = APIClient(base_url="https://billing.example.com")
    client.set_token(token_manager.get_token())
    client._token_manager = token_manager
    yield client
```

Remember to register both in `CLIENT_FIXTURES`.
