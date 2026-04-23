# pytest-api-kit

> Pragmatic scaffolding for API smoke & regression tests.
> Pytest + Requests, with the **observability your team actually wants**: schema validation, snapshot drift detection, and HTML reports that surface endpoint / status / payload shape / description per test.

**[繁體中文](#中文版)** | **English**

---

## Why another API test thing?

Most API test stacks lean one of two ways:

1. **Plugin overkill** — `pytest-plugin-X` + `pytest-plugin-Y` + mock servers + schema registry → weeks before you write the first assertion.
2. **Bare assertions** — raw `requests.get` + `assert resp.status_code == 200` → ships fast but silent to "200 but array is empty" bugs, no drift detection, ugly reports.

`pytest-api-kit` sits in the middle. It's a scaffolding repo with a tiny shared core (`api_kit` package) you clone and adapt. You own the test code; the kit just hands you the plumbing:

- **APIClient** with auto-logging (method, status, size, duration, payload shape)
- **Zero-dep schema validator** — one DSL, 10 lines to read, no jsonschema / pydantic
- **Snapshot drift detection** — auto-saves response baseline on pass, diffs on fail (added/removed fields, type changes, ±30% size drift)
- **Pytest-HTML extras** — adds Endpoint / Status / API Time / Size / Payload shape / Description columns to the built-in report
- **Empty-array warning** — flags "200 OK but `items: []`" responses automatically (silent breakage class)

---

## 60-second demo

```bash
git clone https://github.com/kao273183/pytest-api-kit.git
cd pytest-api-kit
python3 -m venv venv && source venv/bin/activate
pip install -e .
pytest examples/ -v
open report.html
```

You'll see 8 tests pass against [httpbin.org](https://httpbin.org), and `report.html` carries a row per test with these columns filled in:

| Test | Endpoint | Status | API Time | Size | Payload | Description |
|---|---|---|---|---|---|---|
| test_get_200 | GET /get | 200 | 180ms | 298B | args={0k} headers={7k} origin="..."  url="..." | GET /get — simplest possible smoke check. |

Try breaking one of the example assertions — the failure report shows an `API_CHANGED` diagnosis if the response shape drifted, or silence if it didn't (meaning it's a real bug).

---

## What's in the box

```
pytest-api-kit/
├── src/api_kit/              ← the tiny shared core (install once, import everywhere)
│   ├── client.py             ← APIClient: auto-logs every request, tracks last_* attrs
│   ├── schema.py             ← S DSL + validate()
│   ├── snapshot.py           ← save/load/compare JSON response baselines
│   ├── fixtures.py           ← make_client_fixture(), make_auth_client_fixture()
│   └── reporters/
│       └── html_extras.py    ← pytest-html hooks (Endpoint/Status/Size/Payload/Description)
├── examples/
│   ├── conftest.py           ← copy this as your starting point
│   └── test_example.py       ← 8 tests demoing every feature
├── templates/                ← starter files for a new project
│   ├── conftest.py
│   ├── pytest.ini
│   └── config/env.template.yaml
└── docs/
    ├── getting-started.md    ← 30-minute guide
    ├── schema-cookbook.md    ← 10 common response shapes → schema DSL
    └── adapters/
        ├── bearer-token.md
        ├── oauth.md
        └── otp-flow.md
```

---

## 5 features that matter in practice

### 1. Payload-shape logging catches the silent bug class

A passing test that says `status_code == 200` is worth less than you think. This is a real bug we've seen:

```
GET /api/v1/news  →  200 OK
{"total": 42, "records": [], "categories": [...]}
                        ^^^
                        ← records is empty, but the test passed
```

`api_kit` logs this automatically:

```
[INFO] GET https://api.example.com/api/v1/news -> 200 (142 bytes, 95.3ms)
[INFO]   payload: total=42  records[]=0⚠  categories[]=5
[WARN]   ⚠ empty fields: records
```

And the `⚠` tag shows up in the HTML report so you don't miss it.

### 2. Schema validation with no library to learn

```python
from api_kit import validate, S

validate(resp.json(), {
    "total": S.int,
    "records": S.list_of({
        "id": S.any,
        "title": S.str,
        "published_at": S.optional,
    }),
})
```

That's the whole DSL. Error messages carry JSON paths:

```
SchemaError: $.records[0].title: expected str, got NoneType = None
```

### 3. Snapshot drift = free API change detection

Saved per-endpoint JSON baseline (field paths + types + response size). When a test fails, diff against baseline to classify:

- **Fields added/removed/type-changed** → probably a spec change, not a bug
- **Response size ±30% AND ±2KB** → probably data volume change
- **No diff** → probably a real bug

You can wire this into pytest-html's Diagnosis column (see `examples/conftest.py`).

### 4. HTML report that's actually useful

pytest-html's default table is method/status — fine for a one-off run, useless for a team dashboard. With the extras plugin you get:

- **Endpoint** — one column click-sortable
- **Status** — colour-coded (2xx/4xx/5xx)
- **API Time** — colour-coded by latency threshold (green/yellow/red)
- **Size** — bytes/KB auto-formatted
- **Payload** — monospace shape summary + ⚠ for empties (full summary on hover)
- **Description** — first line of docstring + full `__doc__` as tooltip

### 5. Drop-in replacement for raw requests

Every call keeps the familiar `requests.Response` API. You can graduate an existing test suite over gradually — just swap `requests.get` for `api_client.get`.

---

## Install

```bash
# From git (current)
pip install git+https://github.com/kao273183/pytest-api-kit.git

# From PyPI (planned, not yet published)
pip install pytest-api-kit
```

---

## Adapting to your auth flow

Three adapter docs for the common cases:

- **Bearer token** — `docs/adapters/bearer-token.md` (OAuth2 client credentials, API keys, etc.)
- **OAuth with refresh** — `docs/adapters/oauth.md` (with mid-session token refresh)
- **OTP / multi-step login** — `docs/adapters/otp-flow.md` (SMS/Email OTP + AES payload, real-world extracted from production)

---

## Extras (optional, shipped as separate repos)

- **[`pytest-api-kit-aws`](https://github.com/kao273183/pytest-api-kit-aws)** — ECS Fargate + ECR + S3 + CloudFront one-click deploy (CloudFormation + shell scripts)
- **[`pytest-api-kit-dashboard`](https://github.com/kao273183/pytest-api-kit-dashboard)** — Cognito-gated self-service trigger panel for non-engineers to kick off tests and browse reports

---

## Contributing

```bash
git clone https://github.com/kao273183/pytest-api-kit.git
cd pytest-api-kit
python3 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
pytest
```

PRs welcome, especially:
- More auth adapters (SAML, JWT custom claims, mTLS)
- Additional reporter backends (Allure, Slack, Discord)
- Language-agnostic reporter JSON export

---

## License

MIT — see [LICENSE](LICENSE).

Extracted from a production UAT API test framework, stripped of domain-specific bits, and rebuilt to be adoptable by any team in a weekend.

---

## 中文版

### 為什麼又一個 API 測試工具？

API 測試工具通常兩極化：

1. **Plugin 地獄** — 堆 10 個 pytest plugin + mock server + schema registry，設定好要一週
2. **裸 requests** — `assert status == 200` 寫很快，但抓不到「200 但陣列空」這種靜默 bug，報告也難看

`pytest-api-kit` 在兩者中間。是**腳手架 repo**（不是 plugin），你 clone 下來改幾個 config 就能寫第一個 test。共用核心（`api_kit` package）薄薄一層，其他都是你自己的 code。

### 核心功能

1. **`APIClient`** — 每次呼叫自動 log method/status/size/duration/payload shape
2. **零依賴 schema validator** — `validate(data, {"id": S.str, ...})`，10 行讀完
3. **Snapshot drift 偵測** — 自動存 baseline，比對出欄位增減、型別改變、±30% size 漂移
4. **Pytest-HTML 多欄位報告** — Endpoint / Status / API Time / Size / Payload / Description
5. **空陣列警告** — 「回 200 但 `data[]` 是空的」自動標 ⚠

### 快速開始

```bash
git clone https://github.com/kao273183/pytest-api-kit.git
cd pytest-api-kit
python3 -m venv venv && source venv/bin/activate
pip install -e .
pytest examples/ -v
open report.html
```

### 適用場景

- **30+ API 的新創** — 工程師想寫 smoke test 但不想花一週設基礎設施
- **QA 從手測升級到自動化** — 照 example 改就能擴充
- **架構師要 daily UAT regression** — 開箱即用 CI / Docker / Slack 通知

### 延伸模組（獨立 repo）

- **`pytest-api-kit-aws`** — ECS Fargate 一鍵部署（CloudFormation）
- **`pytest-api-kit-dashboard`** — Cognito 自助觸發面板（給非工程使用者）

### 授權

MIT。歡迎 fork 改用在任何公司專案，不用留版權宣告（但提一下很開心）。
