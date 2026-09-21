# AUDIT.md — AlgoRhythm (hospital risk prediction) audit & repair plan

Audit date: 2026-09-21. Scope: `app.py`, `requirements.txt`, `render.yaml`,
templates, `README.md`, repository hygiene.

This document records what was found, what was fixed on branch
`fix/audit-and-repairs`, and what remains to be done.

---

## Findings

### P0 — blocking / security / correctness

| # | Finding | Evidence | Status |
| --- | --- | --- | --- |
| 1 | `requirements.txt` was UTF-16LE with BOM and CRLF, so `pip install -r` fails outright on many toolchains. It also carried the whole TensorFlow/Keras stack that the app never imports. | `file requirements.txt` → `Unicode text, UTF-16, little-endian text, with CRLF line terminators`. Models inspected: `heart_model.pkl`, `diabetes_model.pkl` are `xgboost XGBClassifier`; `preprocessing.pkl` is sklearn + numpy only. No `tensorflow`/`keras` reference inside any pickle. | **Fixed** |
| 2 | `render.yaml` had `buildCommand: ""` (dependencies never installed) and `startCommand: gunicorn app:app`, which ignores Render's `$PORT`. No Python version pin. | `render.yaml` lines 6–7. | **Fixed** |
| 3 | Authentication was cosmetic: `templates/login.html` compared hardcoded credentials in client-side JS (`nurse/nurse123`, `doctor/admin123`) and the server had **no** auth on any route. Every patient endpoint was public. | `login.html` script block; no `session`/decorator usage anywhere in `app.py`. | **Fixed** |
| 4 | Broken edit/navigation flows: `doctor_edit_patient.html` POSTs `/doctor/update` (no route); `nurse_edit_patient.html` POSTs `/nurse/update` (no route); `all_patients.html` links `/doctor/edit/<op>` (no route); `nurse.html` + `nurse_edit_patient.html` link `/nurse/all_patients` (no route); `index.html` was never rendered and fetched `/predict` (no route). | `grep` over `templates/` for URL literals vs. `@app.route` list. | **Fixed** |
| 5 | OP number `f"OP{date}{random.randint(100,999)}"` against a `unique=True` column — a collision raises `IntegrityError` and returns HTTP 500. | `app.py` `add_readmission` / `add_diabetes`. | **Fixed** |

### P1 — hygiene / correctness

| # | Finding | Status |
| --- | --- | --- |
| 6 | `.gitignore` contained only `venv/`; built SQLite DBs were committed. | **Fixed** |
| 7 | Dead/duplicated helpers: unused `safe_int()`; `map_categorical()` defined and never called; `to_int()` duplicated inline; bare `except:` clauses. | **Fixed** |
| 8 | `update_patient` (diabetes branch) rescored with hardcoded placeholder `race`/`gender`/`diag_*`/`admission_type_id`, producing a meaningless risk score. | **Fixed** (see decision below) |
| 9 | `README.md` claimed RandomForest and MLP models (both XGBoost), `instances/` (actual `instance/`), a placeholder clone URL, and had a stray ```` ```yaml ```` block. | **Fixed** |
| 10 | No audit summary / dev plan. | **This document** |

### Lower severity

| # | Finding | Status |
| --- | --- | --- |
| 11 | `all_patients.html` rendered `p.diagnosis`, `p.treatment`, `p.notes` — columns that do not exist on either model, so those cells were always `-`. Now mapped to the real `problem` / `available_doctors` fields. | **Fixed** |
| 12 | `doctor.html` interpolated fetched patient JSON into `innerHTML` unescaped — stored XSS via any patient-supplied text field. An `escapeHtml` helper is now applied to every interpolated value. | **Fixed** |
| 13 | No CSRF protection on any POST form. A per-session token now lives in the signed cookie; a `before_request` hook rejects any unsafe method without a matching `_csrf_token` field or `X-CSRF-Token` header (400). All forms carry the token. | **Fixed** |
| 14 | Five handlers returned `str(e)` with HTTP 500, leaking SQL, file paths, and model internals to the client. A shared `internal_error()` helper logs the real exception server-side and answers with a generic message. | **Fixed** |
| 15 | `flask-cors` was pinned but imported nowhere. | **Fixed** (removed) |
| 16 | `doctor_edit_patient.html` is doctor-only in its field set; the `model` query arg is trusted straight from the URL. | **Still outstanding** — low impact, validated against a known model list |
| 17 | `db.create_all()` at import time is not migration-managed; schema changes need manual handling. | **Still outstanding** |
| 18 | Free-tier Render instances have ephemeral disks, so SQLite data is lost on redeploy. | **Still outstanding** — needs Postgres |

---

## Features added

| # | Feature | Where |
| --- | --- | --- |
| B1 | **Pagination + search** on patient lists (25/page, filters by OP number or name). | `paginate_patients()`, `all_patients.html`, `nurse_all_patients.html` |
| B2 | **Audit log** — records timestamp, actor, role, action, model type, OP number, and detail on create/update/login/logout. Doctor-only viewer. | `AuditLog`, `record_audit()`, `/doctor/audit_log` |
| B3 | **Health check** for deploys — reports DB connectivity and model-load status, 503 when unhealthy. | `/healthz` |
| B4 | **Doctor dashboard** — per-model totals, high-risk count (risk ≥ 0.7), average risk, and the 5 most recent records. | `/doctor/dashboard`, `dashboard.html` |
| B5 | **CSV export** of patient lists, honouring the active search filter. | `/doctor/export/<model>.csv` |
| B6 | **Test suite** — auth, CSRF, role separation, OP-number uniqueness, pagination, export, audit log, `/healthz`. | `tests/` |

---

## Decision on finding 8 (diabetes risk rescoring)

Two options were considered:

1. **Stop recomputing** the diabetes risk score on edit.
2. **Store the real feature vector** at creation and rescore from it.

Option 2 was chosen, implemented minimally: a nullable `model_features TEXT`
column holds the JSON of the exact 44-feature vector used for the original
prediction. On edit, the vector is restored and refreshed with the patient's
current clinical values (the columns that are both stored and model features),
then rescored. A migration helper adds the column to pre-existing SQLite files.

For records created **before** this change there is no stored vector, so the
score is intentionally left untouched rather than recomputed from placeholders —
scoring with invented `race`/`gender`/`diag_*` values is worse than leaving a
previously valid score alone.

---

## Prioritized dev plan

1. **P0 — done on this branch.** Encoding/deps, deploy config, server-side auth, dead routes, collision-safe OP numbers.
2. **P1 — next.** Add CSRF protection; escape patient-supplied values in `doctor.html`; reconcile the phantom `diagnosis`/`treatment`/`notes` columns; add a test suite (pytest + Flask test client) covering login, role separation, add/edit flows, and OP-number uniqueness under collision.
3. **P2 — schema & data.** Introduce Alembic/Flask-Migrate; move to Postgres (or a mounted disk) so data survives Redeploys; drop `flask-cors` if it stays unused.
4. **P3 — product.** Per-doctor accounts, audit log of who changed which record, PDF/CSV export, model-training UI.

## Verification performed

- `python3 -m py_compile app.py` and every file under `tests/` — passes.
- `requirements.txt` decodes as UTF-8 with no BOM.
- `python3 tools/check_routes.py` — every URL literal in `templates/` resolves to a declared Flask rule (19 routes).
- `grep` confirms no `str(e)` remains in a 500 response, and no unescaped `innerHTML` interpolation remains in `doctor.html`.
- `flask-cors` is absent from `requirements.txt` and is never imported.
- AST pass over `app.py` confirms no undefined names.

**The test suite was NOT executed.** This environment has no `pip` module, no
PyPI egress, and only Python 3.14 — for which the pinned `xgboost==3.0.0` and
`pandas==2.2.3` wheels do not exist. The tests are syntax-checked only. Runtime
behaviour is unverified and must be confirmed on a machine with the pinned
Python 3.11 and the requirements installed.
