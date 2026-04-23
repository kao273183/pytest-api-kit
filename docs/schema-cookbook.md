# Schema cookbook

10 common response patterns → how to write them in the `S` DSL.

## 1. Simple object

```json
{"id": "u_123", "name": "Alice", "active": true}
```

```python
validate(data, {
    "id": S.str,
    "name": S.str,
    "active": S.bool,
})
```

## 2. Envelope with list

```json
{"total": 42, "items": [...]}
```

```python
validate(data, {
    "total": S.int,
    "items": S.list_of(),  # don't care about item shape
})
```

## 3. Envelope with list + item schema

```json
{"total": 42, "items": [{"id": "a", "name": "..."}]}
```

```python
validate(data, {
    "total": S.int,
    "items": S.list_of({
        "id": S.str,
        "name": S.str,
    }),
})
```

## 4. Optional fields

```python
validate(data, {
    "id": S.str,
    "display_name": S.optional,  # may be missing OR null
})
```

> Note: `S.optional` means **present-but-null is also OK**. If the key must be
> present but the value can be null, use `S.any` and handle null explicitly.

## 5. Nested object

```json
{"user": {"profile": {"email": "..."}}}
```

```python
validate(data, {
    "user": {
        "profile": {
            "email": S.str,
        }
    }
})
```

## 6. Union types — skip them

The DSL intentionally doesn't support `str | int`. If a field is a union, just
assert the key exists:

```python
validate(data, {
    "value": S.any,  # could be str or int
})
# Then narrow in code:
v = data["value"]
assert isinstance(v, (str, int))
```

## 7. Root-level list

```json
[{"id": 1}, {"id": 2}]
```

```python
validate(data, S.list_of({"id": S.int}))
```

## 8. Paginated response

```json
{"data": [...], "meta": {"pagination": {"page": 1, "pageSize": 10, "total": 42}}}
```

```python
validate(data, {
    "data": S.list_of(),
    "meta": {
        "pagination": {
            "page": S.int,
            "pageSize": S.int,
            "total": S.int,
        }
    }
})
```

## 9. Strapi-style `{data: [{attributes: ...}]}`

```python
validate(data, {
    "data": S.list_of({
        "id": S.any,
        "attributes": S.dict,
    }),
    "meta": S.dict,
})
```

## 10. Error response

```json
{"error": {"code": "NOT_FOUND", "message": "..."}}
```

```python
validate(data, {
    "error": {
        "code": S.str,
        "message": S.str,
    }
})
```

---

## Anti-patterns

### Don't validate every field

The point is to catch *shape* changes, not to duplicate your API spec in Python.
Validate the fields you'd actually read in the test, plus any you care about
when the API changes.

### Don't reuse schemas between versions

```python
# NO — coupling v1 and v2 together
NEWS_SCHEMA = {...}

class TestV1:
    def test_get(self, client):
        validate(client.get("/api/v1/news").json(), NEWS_SCHEMA)

class TestV2:
    def test_get(self, client):
        validate(client.get("/api/v2/news").json(), NEWS_SCHEMA)
```

Write them separately. When v2 drops a field, you want the v1 test to keep
passing. Coupled schemas force both to break.

### Don't check types in assertions AND schema

```python
# Redundant — validate() already raised if id was an int
validate(data, {"id": S.str})
assert isinstance(data["id"], str)
```

Pick one. Prefer `validate()` — the error messages include JSON paths.
