"""
Reusable pytest fixture helpers.

Typical usage in your project's conftest.py:

    import pytest
    from api_kit.fixtures import make_client_fixture

    api_client = make_client_fixture("https://api.example.com")

    # Or if you need custom headers / auth:
    from api_kit import APIClient

    @pytest.fixture(scope="session")
    def api_client():
        client = APIClient(
            base_url="https://api.example.com",
            extra_headers={"X-Tenant-ID": "acme"},
        )
        yield client
        client.session.close()
"""
from __future__ import annotations

from typing import Callable, Dict, Optional

import pytest

from .client import APIClient


def make_client_fixture(
    base_url: str,
    extra_headers: Optional[Dict[str, str]] = None,
    scope: str = "session",
    user_agent: str = "pytest-api-kit/1.0",
) -> Callable:
    """Factory that returns a pytest fixture yielding a fresh APIClient.

    Example:
        news_client = make_client_fixture("https://news.example.com")
    """
    @pytest.fixture(scope=scope)
    def _fixture():
        client = APIClient(
            base_url=base_url,
            extra_headers=extra_headers,
            user_agent=user_agent,
        )
        yield client
        client.session.close()

    return _fixture


def make_auth_client_fixture(
    base_url: str,
    token_provider: Callable[[], str],
    extra_headers: Optional[Dict[str, str]] = None,
    scope: str = "session",
) -> Callable:
    """Factory for a client that auto-fetches a Bearer token on init.

    ``token_provider`` is a zero-arg callable that returns a fresh token
    (it's only called once per fixture scope — plug your own refresh logic if
    you need mid-session renewal).

    Example:
        auth_client = make_auth_client_fixture(
            "https://api.example.com",
            token_provider=lambda: my_auth_flow(),
        )
    """
    @pytest.fixture(scope=scope)
    def _fixture():
        client = APIClient(base_url=base_url, extra_headers=extra_headers)
        token = token_provider()
        client.set_token(token)
        yield client
        client.session.close()

    return _fixture
