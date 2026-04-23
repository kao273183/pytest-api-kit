# Design

**[繁體中文](#中文版) | English**

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

---

## 中文版

這份文件是**活的 spec** — 短、有態度、可以引用。每次 review PR 時如果跟這份衝突，先拒絕，要求作者把對應段落一起改掉再 merge。

### 1. 範圍（Scope）

#### 做什麼 ✅

- **給 pytest 寫 API smoke / regression test 的腳手架** — 建 client、寫 assertion、產報告的基本 workflow
- **可觀測性工具** — payload shape 自動 log、response size 追蹤、空陣列警告、snapshot drift 偵測
- **零依賴的 schema 驗證** — 小型 DSL，夠用於 90% 的 response 結構驗證
- **Pytest-HTML 擴充欄位** — Endpoint / Status / API Time / Size / Payload / Description 讓 team 能共讀
- **Auth adapter 文件** — Bearer / OAuth / OTP / SAML 等接法寫成教學，不用 fork core

#### 不做什麼 ❌

- **Mock / record-replay server** — 用 `responses` / `vcrpy` / `pytest-httpx`
- **Contract testing** — 用 Pact、Spectral
- **壓力測試** — 用 Locust、k6
- **UI / browser 測試** — 用 Playwright、Selenium
- **測試資料工廠** — 用 `factory-boy` 或手寫 fixture
- **CI runner / 儀表板部署** — 已拆到另外兩個 repo：`pytest-api-kit-aws`、`pytest-api-kit-dashboard`

遇到「out of scope」的功能請求 → 直接引用本段 close issue。

### 2. 穩定性承諾（Stability contract）

從 0.2.0 起遵守 semver；0.1.0 是「盡力穩定」。公開介面範圍：

#### 穩定 — 同 major 內不會動

```python
from api_kit import (
    APIClient,
    S, SchemaError, validate,
    capture_schema, compare_with_snapshot, load_snapshot, save_snapshot,
)
from api_kit.fixtures import make_client_fixture, make_auth_client_fixture
from api_kit.reporters.html_extras import CLIENT_FIXTURES, install_html_extras
```

`APIClient.{get, post, put, patch, delete, request, set_token, set_header}` 的簽名不動；可加新的 optional kwargs。

Schema DSL 的 `S.str / S.int / S.any / S.optional / S.list_of(...)` 等值穩定。

#### 內部 — 可能隨時改

- 底線開頭（`_summarize_payload` 等）
- `api_kit.reporters.html_extras._pytest_*` hook — 只能透過 `install_html_extras()` 間接使用
- Snapshot 檔案的磁碟格式 — load/compare API 穩定，但不要自己 parse JSON
- html_extras 注入的 CSS / HTML — 顏色、欄寬、格式保留調整空間

需要倚賴「內部」項目 → 開 issue 要求升級成 public。

### 3. 設計 rationale（FAQ）

#### 為什麼不用 `jsonschema` 或 `pydantic`？

因為 **零依賴** 是主打。新上 pytest 的 team 常常卡在相依性衝突一整天。S DSL 用 100 行覆蓋 90% 真實世界 response — 需要完整 JSON Schema 再 `pip install jsonschema` 搭配用，沒禁止。

#### 為什麼不做成 `pytest` plugin（entry points / hook / config）？

對這類問題，**腳手架 > plugin**：

- Team 本來就會互相 copy fixture — 我們用 `templates/` / `examples/` 擁抱這行為
- 零設定檔要學 — 裝完 `from api_kit import ...` 就上工
- Fork `conftest.py` 改 hook 比 fork plugin 的 hook implementation 容易 100 倍

#### 為什麼 AWS / dashboard 拆成獨立 repo？

因為 90% user 不需要。`pip install pytest-api-kit` 不應該順便 `pip install boto3`。基礎設施的表面積比測試框架本體大 10 倍，拆開獨立演進更健康。

#### 為什麼自己管 HTML 欄位，不做成可擴充 event bus？

因為要顯示的三個核心欄（Endpoint / Status / Payload）都來自同一組 `APIClient.last_*` 屬性 — 抽象化只會逼每個 user 都去 config 該顯示什麼。模板刻意 opinionated — 需要不一樣的直接 **整個換掉** `html_extras.py`，不要去擴充它。

#### 為什麼在 client 藏一個 `_last_response_data`？

讓 pytest-html hook 和 snapshot hook 都能拿到上次 parse 過的 JSON，不用重 parse。用 `_` 前綴表示 test 不該直接讀；官方 snapshot example 讀它因為它本來就是 kit 的一部分。

#### 為什麼 `install_html_extras()` 去 monkey-patch caller 的 `globals()`？

因為 pytest **只在 module top-level** 找 `pytest_html_*` hook — user 一定會忘記把 hook re-export。Monkey-patch 是「最少 surprise」的做法，一個 call 搞定。

#### 為什麼用一個 module-level 可變 list `CLIENT_FIXTURES` 讓 user `.extend()`？

因為 reporter 要知道哪些 fixture 名字是 `APIClient` instance，而 pytest 沒有 introspect fixture type 的 API（只能靠名字）。共用一個 list + `.extend()` 是「最小可行」的 user-facing API。

### 4. Review checklist

Review PR 時，確認：

- [ ] 沒踩進 §1 的「不做什麼」清單
- [ ] 公開 API 有改 → §2 有對應更新 + CHANGELOG 一行
- [ ] 如果改動和 §3 某個 rationale 矛盾 → PR 本身要更新那段
- [ ] 沒加新的第三方相依（零依賴承諾）
- [ ] `pytest examples/ -v` 仍綠（CI 會擋）
- [ ] 新的 public behaviour 至少在 `examples/` 裡有一個 test cover

---

**這份文件是 load-bearing（承重的）**。有疑問直接貼連結 — 一旦新答案跟這裡矛盾，不是先更新文件，就是拒絕新答案。
