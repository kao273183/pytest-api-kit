# Contributing

Thanks for looking — short guide to get you productive fast.

**[繁體中文](#中文版) | English**

---

## Before you start

Read **[`docs/design.md`](docs/design.md)** first. It spells out:

- What's in scope (API smoke scaffolding + observability aids)
- What's out (mock servers / contract tests / load tests — rejected on sight)
- The stability contract (which imports can never break inside a major)
- FAQ-style rationale for six common "why not X" questions

If your idea clashes with anything there, either update `design.md` in the
same PR (with reasoning), or consider whether a companion repo fits better.

---

## Local setup

```bash
git clone https://github.com/kao273183/pytest-api-kit.git
cd pytest-api-kit
python3 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"

# Verify
pytest examples/ -v   # 6 tests should pass
```

Python 3.9+ required. CI runs the matrix on 3.9 / 3.10 / 3.11 / 3.12.

---

## Making a change

### Branch naming

- `feat/<short-description>` — new feature
- `fix/<short-description>` — bug fix
- `docs/<short-description>` — docs only
- `chore/<short-description>` — tooling / CI / deps

### Commit messages

Conventional Commits style — scopes match directories where helpful:

```
feat(client): support retries on idempotent methods
fix(snapshot): handle None size_bytes in drift calculation
docs(schema-cookbook): add Strapi v5 example
chore(ci): bump actions/setup-python to v5
```

### Running tests

```bash
# Full example suite (what CI runs)
pytest examples/ -v

# With HTML report to eyeball the reporter columns
pytest examples/ -v --html=report.html --self-contained-html
open report.html
```

### Before opening a PR — checklist

- [ ] `pytest examples/ -v` is green
- [ ] No new third-party dependencies (the zero-dep promise in §3 of design.md)
- [ ] Public API change? — update §2 of `docs/design.md` (stability contract)
- [ ] Behavioural change? — at least one new test in `examples/test_example.py`
- [ ] New adapter / auth flow? — add a doc under `docs/adapters/`

---

## Pull request flow

1. Fork, branch off `main`
2. Write + commit + push to your fork
3. Open PR against `kao273183/pytest-api-kit:main`
4. Fill in the PR template (appears automatically)
5. CI runs across Python 3.9–3.12 matrix — all must pass
6. Review turnaround: best-effort within a week. Ping here if longer.

Small PRs get reviewed first. If you're doing something big, open an issue
to discuss design before writing the code — saves both sides time.

---

## Issues

- **Bugs**: include Python version, minimal repro, observed vs expected
- **Features**: describe the use case first, not the proposed API. If it
  crosses a line in `design.md §1`, I'll close with a link — no hard feelings
- **Questions**: GitHub Discussions is fine too

---

## Maintainer notes (for future me / co-maintainers)

- **Releases** — bump `version` in `pyproject.toml`, tag `vX.Y.Z`, push tag.
  (Once Trusted Publishing is set up, tagging triggers automatic PyPI upload.)
- **Scope creep** — when in doubt, reject. A small, opinionated kit that
  does one thing well beats a kitchen sink.
- **Dependency adds** — re-read the zero-dep promise. If you really need one,
  discuss in an issue first + document in `design.md §3`.

---

## Licence

By contributing, you agree your contribution will be MIT-licensed (same as
the project).

---

## 中文版

歡迎貢獻，簡短指引讓你快速上手。

### 開始前先讀

**[`docs/design.md`](docs/design.md)** — 裡面寫明：

- 範圍內：API smoke 腳手架 + 可觀測性工具
- 範圍外：mock server / contract test / 壓測 — 一律拒絕
- 穩定性承諾：哪些 import 在同 major 內保證不動
- 六個常見「為什麼不做 X」的 FAQ

如果你的想法跟文件衝突，要嘛同一個 PR 更新 `design.md` 附說明，要嘛考慮做成 companion repo（像 `pytest-api-kit-aws`）比較合適。

### 本地環境

```bash
git clone https://github.com/kao273183/pytest-api-kit.git
cd pytest-api-kit
python3 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
pytest examples/ -v   # 應通過 6 個 test
```

需要 Python 3.9+。CI 跑 3.9 / 3.10 / 3.11 / 3.12 矩陣。

### Branch 命名

- `feat/<短描述>` — 新功能
- `fix/<短描述>` — bug 修正
- `docs/<短描述>` — 純文件
- `chore/<短描述>` — tooling / CI / 相依

### Commit 訊息

Conventional Commits 格式：

```
feat(client): 支援 idempotent method 自動 retry
fix(snapshot): 處理 size_bytes 為 None 的情況
docs(schema-cookbook): 新增 Strapi v5 範例
chore(ci): 升級 actions/setup-python 到 v5
```

### 開 PR 前 checklist

- [ ] `pytest examples/ -v` 綠
- [ ] 沒加新第三方相依（design.md §3 的零依賴承諾）
- [ ] 改到 public API → 更新 `docs/design.md` §2（穩定性承諾）
- [ ] 行為有變 → `examples/test_example.py` 至少加一個 test
- [ ] 加新 adapter → 在 `docs/adapters/` 加文件

### PR 流程

1. Fork、從 `main` 開分支
2. 寫 + commit + push
3. 對 `kao273183/pytest-api-kit:main` 開 PR
4. 填 PR template（自動帶入）
5. CI 跑 Python 3.9–3.12 矩陣，全綠才能 merge
6. Review 節奏：盡量一週內回覆，久了可以在 PR 下留言 ping

小 PR 優先 review。大改動請先開 issue 討論設計再寫 code。

### Issue

- **Bug**：附 Python 版本、最小重現、觀察 vs 預期
- **Feature**：先描述 use case，不要直接 propose API。如果踩到 `design.md §1` 的線，會被 close 並附連結
- **問題**：GitHub Discussions 也可

### 授權

貢獻即視為同意以 MIT 授權釋出（與專案一致）。
