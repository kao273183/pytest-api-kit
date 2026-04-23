# Design

Living document — short and opinionated. Updates require a follow-up commit
with rationale. If you're reviewing a PR that contradicts anything here,
reject first and ask the author to update this file as part of the change.

---

## 1. Scope

### In scope ✅

- **API smoke / regression scaffolding for pytest** — the workflow of
  "compose an HTTP client, write assertions, generate a report"
- **Observability aids** — auto-log of payload shape, response size, empty-array
  warnings, snapshot drift
- **Zero-dep schema validation** — tiny DSL good enough for 90% of response
  shape checks
- **Pytest-HTML extras** — extra columns that make reports team-readable
- **Adapter documentation** — how to graft on your own auth flow (Bearer /
  OAuth / OTP / SAML /…) without forking the core

### Out of scope ❌

- **Mock / record-replay servers** — use `responses`, `vcrpy`, `pytest-httpx`
- **Contract testing** — use Pact, Spectral
- **Load testing** — use Locust, k6
- **Browser / UI tests** — use Playwright, Selenium
- **Test data factories** — orthogonal; use `factory-boy` or handwritten fixtures
- **CI runner / dashboard hosting** — moved to companion repos
  (`pytest-api-kit-aws`, `pytest-api-kit-dashboard`)

Reject feature requests that push into the "out of scope" list. Link here
in the close message.

---

## 2. Stability contract

This project follows semver as of 0.2.0 (the 0.1.0 release is
"best-effort stable"). The public surface is:

### Stable — won't change within a major version

```python
from api_kit import (
    APIClient,
    S, SchemaError, validate,
    capture_schema, compare_with_snapshot, load_snapshot, save_snapshot,
)
from api_kit.fixtures import make_client_fixture, make_auth_client_fixture
from api_kit.reporters.html_extras import (
    CLIENT_FIXTURES,
    install_html_extras,
)
```

Method signatures on `APIClient.{get, post, put, patch, delete, request,
set_token, set_header}` won't change; new optional kwargs may be added.

Schema DSL values (`S.str`, `S.int`, `S.any`, `S.optional`, `S.list_of(...)`,
nested dict schemas) are stable.

### Internal — may change without notice

- Anything starting with `_` (e.g. `api_kit.client._summarize_payload`)
- `api_kit.reporters.html_extras._pytest_*` hook functions — consumed only
  via `install_html_extras()`
- Snapshot file format on disk — load/compare API is stable, but don't
  parse the JSON yourself
- The HTML / CSS that html_extras injects into pytest-html — we reserve the
  right to change colours, column widths, formatting

If you want to rely on something in the "internal" list, open an issue so
we can promote it properly.

---

## 3. Design rationale (FAQ)

### Why not `jsonschema` or `pydantic`?

Because **zero dependencies** is the main selling point. Teams onboarding
onto pytest for the first time lose hours to dependency conflicts. The
S DSL covers ~90% of real-world response shapes in 100 lines. If someone
needs full JSON Schema, they can `pip install jsonschema` and use it
alongside; it's not forbidden.

### Why not a `pytest` plugin (entry points, hooks, config options)?

Scaffolding > plugins for this problem class:

- Teams already copy-paste test fixtures around; we embrace that with
  `templates/` and `examples/` rather than fight it
- No `setup.cfg` or `pytest.ini` options to learn — `pip install` then
  `from api_kit import ...`
- Forking `conftest.py` to customise a hook is 100× easier than forking
  a plugin's hook implementation

### Why split AWS / dashboard into separate repos?

Because 90% of users don't want them. `pip install pytest-api-kit` should
never `pip install boto3` as a side effect. Infrastructure has a 10× larger
surface area than the test framework itself — keeping it separate lets
them evolve independently.

### Why own the HTML reporter columns instead of a generic event bus?

Because the three columns that matter (Endpoint / Status / Payload) all
come from the same `APIClient.last_*` attributes, and generalising would
mean every user has to configure what gets shown. The template is
opinionated on purpose — replace the whole `html_extras.py` if you need
something different; don't extend it.

### Why track `_last_response_data` on the client as a hidden attribute?

So that the pytest-html hook and the snapshot save/diff hook can find
the last parsed JSON without re-parsing. It's private (`_` prefix) so
tests shouldn't read it; the snapshot examples do because they're part
of the kit.

### Why does `install_html_extras()` monkey-patch `globals()` of the caller?

Because pytest discovers `pytest_html_*` hooks at module scope only.
Teams would forget to re-export them otherwise. The monkey-patch is the
least-surprise way to make one call do the right thing.

### Why is there a `CLIENT_FIXTURES` module-level list that users mutate?

Because the reporter needs to know fixture names to grab the right
`APIClient` instance per test, and there's no way to introspect pytest
fixtures by type (they're by name). A shared list with `.extend()` is
the smallest user-facing API that works.

---

## 4. Review checklist for PRs

When reviewing a change, confirm:

- [ ] Doesn't cross into the "out of scope" list in §1
- [ ] Public API changes have a matching update in §2 (and a CHANGELOG line)
- [ ] If the change contradicts any §3 rationale, the PR updates that section
- [ ] No new third-party dependencies (the zero-dep promise)
- [ ] `pytest examples/ -v` still passes (CI enforces this)
- [ ] New public behaviour has at least one test in `examples/`

---

**This document is load-bearing.** When in doubt, link here in the
conversation — the moment a new answer diverges from this file, either
update the file first or reject the new answer.
