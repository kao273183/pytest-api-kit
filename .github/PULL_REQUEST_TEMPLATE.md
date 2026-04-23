<!--
  Thanks for the contribution! The checklist below mirrors CONTRIBUTING.md
  and docs/design.md — fill what applies, delete what doesn't.
-->

## Summary

<!-- One-paragraph description of what this PR changes and why. -->

## Type of change

- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking, additive)
- [ ] Breaking change (bumps the major once released)
- [ ] Docs / infra / chore only

## Related issue

Closes #<!-- issue number, or "N/A" if none -->

---

## Pre-flight checklist

<!-- Same checklist as CONTRIBUTING.md — verify each before requesting review. -->

- [ ] `pytest examples/ -v` passes locally
- [ ] **No new third-party dependencies** (the zero-dep promise — see `docs/design.md` §3)
- [ ] Behavioural change has at least one new / updated test in `examples/`
- [ ] Public API change (anything in `api_kit/__init__.py` re-exports)?
      → updated `docs/design.md` §2 **stability contract** in this PR
- [ ] Crosses a line in `docs/design.md` §1 **scope**?
      → updated that section in this PR with rationale
- [ ] New auth adapter / recipe? → added a doc under `docs/adapters/`

## How to verify

<!--
  Steps a reviewer can run to verify the change. For a new feature, show
  the minimal before/after behaviour — ideally a code snippet.
-->

```python
# Example:
from api_kit import APIClient

client = APIClient(base_url="https://httpbin.org")
# before: …
# after:  …
```

## Screenshots / report samples (optional)

<!-- For pytest-html reporter changes, drop a screenshot of the new report. -->
