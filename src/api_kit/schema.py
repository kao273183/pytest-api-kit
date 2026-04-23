"""
Zero-dependency schema validator.

Validates JSON responses against a minimal dict-of-type-markers DSL:

    from api_kit import validate, S

    validate(resp.json(), {
        "total": S.int,
        "records": S.list_of({
            "id": S.any,
            "title": S.str,
            "published_at": S.optional,
        }),
    })

Markers:
    S.str / S.int / S.float / S.bool / S.dict  — exact type
    S.any                                      — any non-None value
    S.optional                                 — key may be missing or None
    S.list_of(item_schema)                     — list, optionally validate first item

Raises SchemaError with a clear JSON path on mismatch.
"""
from __future__ import annotations


class SchemaError(AssertionError):
    """Raised when response doesn't match schema."""
    pass


class S:
    """Schema type markers."""
    str = "str"
    int = "int"
    float = "float"
    bool = "bool"
    any = "any"          # any non-None value
    optional = "optional"  # can be missing or None
    dict = "dict"

    @staticmethod
    def list_of(item_schema=None):
        """List with optional item schema validation."""
        return ("list", item_schema)


def validate(data, schema, path: str = "$") -> None:
    """Validate data against schema; raise SchemaError with JSON path on mismatch."""
    if isinstance(schema, dict):
        if not isinstance(data, dict):
            raise SchemaError(f"{path}: expected dict, got {type(data).__name__}")
        for key, expected in schema.items():
            if expected == S.optional:
                continue
            if key not in data:
                raise SchemaError(f"{path}.{key}: missing required key")
            _check_value(data[key], expected, f"{path}.{key}")

    elif isinstance(schema, tuple) and schema[0] == "list":
        if not isinstance(data, list):
            raise SchemaError(f"{path}: expected list, got {type(data).__name__}")
        item_schema = schema[1]
        if item_schema and data:
            # Validate first item only (performance)
            validate(data[0], item_schema, f"{path}[0]")

    elif isinstance(schema, str):
        _check_value(data, schema, path)


def _check_value(value, expected, path: str) -> None:
    if expected == S.any:
        if value is None:
            raise SchemaError(f"{path}: expected non-None value")
        return

    if expected == S.optional:
        return

    if isinstance(expected, tuple) and expected[0] == "list":
        if not isinstance(value, list):
            raise SchemaError(f"{path}: expected list, got {type(value).__name__}")
        item_schema = expected[1]
        if item_schema and value:
            validate(value[0], item_schema, f"{path}[0]")
        return

    if isinstance(expected, dict):
        validate(value, expected, path)
        return

    type_map = {
        "str": str,
        "int": int,
        "float": (int, float),
        "bool": bool,
        "dict": dict,
    }
    expected_type = type_map.get(expected)
    if expected_type and not isinstance(value, expected_type):
        raise SchemaError(
            f"{path}: expected {expected}, got {type(value).__name__} = {repr(value)[:100]}"
        )
