"""pytest-api-kit — pragmatic scaffolding for API smoke / regression tests."""

__version__ = "0.1.0"

from .client import APIClient
from .schema import S, SchemaError, validate
from .snapshot import (
    capture_schema,
    compare_with_snapshot,
    load_snapshot,
    save_snapshot,
)

__all__ = [
    "APIClient",
    "S",
    "SchemaError",
    "validate",
    "capture_schema",
    "compare_with_snapshot",
    "load_snapshot",
    "save_snapshot",
]
