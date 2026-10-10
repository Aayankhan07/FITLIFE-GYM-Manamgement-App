# FitLife Gym Management System — Architecture Review

**Reviewed document:** `architecture.md` (v2.0.0, October 2026)
**Scope:** Analysis, fixes, upgrades, and better alternatives
**Method:** Static review of the design document only. No source code was available, so every finding about implementation is "as described", and each should be verified against the codebase.

---

## 1. Verdict

The design is clean and well-organized: a layered structure, a sensible async worker model, a good design-token system, and stateless services. It reads like a strong **single-site desktop app**.

It is **not yet safe or correct as a multi-branch, multi-user system**. The weak points are structural, not cosmetic:

| # | Core problem | Severity |
|---|---|---|
| 1 | Silent auto-failover to local SQLite causes **split-brain data** in a multi-client deployment | Critical |
| 2 | Every desktop client talks **directly to the database**, so RBAC and audit are client-side and bypassable | Critical |
| 3 | The scheduler runs inside each client, so every open client runs the same jobs and **duplicates** them | High |
| 4 | Sensitive PII (national ID, biometrics, photos) with no stated encryption, retention, or consent model | High |
| 5 | The AI service likely ships member data to a third-party LLM from the client, with the API key on the client | High |
| 6 | Schema gaps: no subscription history, cascade-delete risk on financial records, no migration tooling | High |
| 7 | The "verification" section proves very little (syntax errors, 4 test areas) | Medium |
| 8 | Several UI/accessibility claims are inaccurate or fail WCAG contrast | Medium |

**Recommendation in one line:** pull the API tier forward from "Phase 2" to "Phase 1", drop automatic SQLite failover, and standardize on one database engine.

---

## 2. Critical Findings and Fixes

### 2.1 Silent SQLite failover creates split-brain data (Critical)

**What the doc says:** If MS SQL Server is unreachable, the app "seamlessly" switches to a local SQLite file and keeps working (§2.4, §6.1).

**Why it breaks:**
- In a multi-branch deployment, each client that loses connectivity starts writing to its **own private SQLite file**. Payments, check-ins, and member edits then exist on one machine only.
- Nothing in the document describes sync or reconciliation. When the network returns, those records are either lost or must be merged by hand.
- Financial data (payments, invoices) is the worst place for this. A cashier could take payment in fallback mode and the record never reaches the central ledger.
- A regex-based T-SQL → SQLite translator is fragile. It handles the listed functions (`DATEADD`, `DATEDIFF`, `MONTH`, `YEAR`) but breaks on `TOP`, `OUTPUT`, `MERGE`, `ISNULL`, `CONVERT`, string concatenation with `+`, CTE differences, and `IDENTITY` vs `AUTOINCREMENT`. Every new query risks a dialect bug that only shows up in fallback mode, the mode that is least tested.
- The two schemas (`schema_sqlite.sql` plus the MS SQL schema) will drift without a migration tool.

**Fix (minimum):**
1. Remove automatic failover. Make SQLite an **explicit, user-selected "Standalone / Single-PC mode"** chosen at install time, never a runtime fallback.
2. When the primary DB is unreachable in networked mode, show a clear **"Offline: read-only"** banner and block writes. Optionally queue a small, well-defined set of offline-safe actions (see 4.2).
3. Add a CI job that runs the **same test suite against both engines**.

**Better:** use one dialect-neutral data layer (SQLAlchemy Core or ORM) instead of regex translation. See §5.

### 2.2 Clients connect straight to the database (Critical)

**What the doc says:** Services run inside the desktop app and use a connection pool to MS SQL Server over the LAN. RBAC is enforced in the application (§4).

**Why it breaks:**
- Each client machine holds DB credentials. Anyone who can read the app config or memory can connect with a SQL client and bypass RBAC entirely: read all members, edit payments, delete audit rows.
- RBAC checks in client code are a UI convenience, not a security boundary. A modified client is trusted equally.
- "Immutable audit log" is not immutable if the same DB account that the client uses can `UPDATE` or `DELETE` it.
- Business rules (discount limits, refund rules, lockout counters) can be skipped by any non-official client.
- Brute-force lockout is stored in `users` and enforced by client code, so it is bypassable.

**Fix (minimum, without a full rewrite):**
1. Use **least-privilege DB accounts**: the app account gets `INSERT` only on `audit_logs` (no `UPDATE`/`DELETE`), and no DDL rights.
2. Move secrets out of plain config files into the OS credential store (Windows Credential Manager via `keyring`).
3. Add DB-side protection for the audit table (see 4.4).

**Real fix:** introduce the API tier now (§5). The server owns the DB credentials, enforces RBAC and business rules, and writes the audit trail. Clients hold only a short-lived token.

### 2.3 Scheduler runs in every client (High)

**What the doc says:** `BackgroundScheduler` runs on a daemon thread inside the app and triggers expiry audits, overdue checks, and system alerts (§2.2).

**Why it breaks:** With N clients open (front desk, manager, two trainers), the same job runs N times. That means duplicate alerts, duplicate overdue fees if the job writes anything, and race conditions on updates. When no client is open overnight, nothing runs at all, so memberships expire without any audit.

**Fix:**
- **Short term:** acquire a DB-level job lock (a `scheduled_jobs` row with `locked_by`, `locked_until`, `last_run`) so only one instance runs each job, and make every job **idempotent**.
- **Proper:** run scheduled jobs on the server (a Windows Service, systemd unit, or the API process with a worker like APScheduler/Celery/RQ), independent of any UI.

---

## 3. High-Severity Findings and Fixes

### 3.1 PII, biometrics, and data protection (High)

The schema stores CNIC/national ID, emergency contacts, progress photos, body measurements, and `Biometric` attendance. The document does not mention encryption at rest, field-level protection, retention, or consent.

**Fixes:**
- Encrypt sensitive columns (national ID, emergency contacts) at the application level or via DB features (SQL Server Always Encrypted / `pgcrypto`). Keep keys outside the DB.
- **Never store raw biometric templates** in the app DB. Keep them on the biometric device or vendor system and store only an opaque reference ID.
- Store progress photos in encrypted object/file storage with access control, not as blobs in a general table.
- Define **retention rules** (for example, purge inactive members' sensitive fields after a set period) and a member **data export/erasure** process.
- Mask national ID in the UI by default (`35202-*******-1`) with an audited "reveal" action.
- Check the data-protection obligations that apply where you operate. This is a legal question, so confirm with qualified counsel.

### 3.2 AI service data flow (High)

The `ai_service` calls an external LLM provider with workout/diet prompts, apparently from the client.

**Risks:** the API key is shipped in or readable by each client, member data (weight, measurements, goals, possibly health notes) leaves the system, and there is no mention of cost control or output safety.

**Fixes:**
- Route all LLM calls through the **server**. The key lives only there.
- Send only the minimum necessary, **de-identified** data (age band, goal, measurements) and never name, national ID, or phone.
- Get explicit member consent before using their data for AI features, and log each call (who, what category, token count) for audit and cost.
- Add per-user and per-branch **rate limits and budgets**.
- Add guardrails: diet/workout output must carry a disclaimer, must not give medical advice, and members who report injuries, pregnancy, or medical conditions should be directed to a professional. Require a **trainer review step** before AI-generated plans become a member's active plan.
- Use structured (JSON schema) outputs so plans are validated before saving.

### 3.3 Schema gaps and risks (High)

| Issue | Why it matters | Fix |
|---|---|---|
| `members` holds only an "active membership plan FK" | No history of renewals, upgrades, freezes, or lapses; revenue and retention analytics become unreliable | Add a **`subscriptions`** table (`member_id`, `plan_id`, `start`, `end`, `status`, `price_at_purchase`, `frozen_from/to`) |
| "Explicit foreign key cascades" | A cascade delete on `members` can wipe payments/invoices | Use `ON DELETE RESTRICT` for financial tables; use **soft delete** (`deleted_at`) for members and anything referenced by money |
| `payments` links to `members` only in the ER diagram; `invoices` is missing from it | Payment-to-invoice allocation (partial payments) is undefined | Model `invoices` → `invoice_lines` → `payment_allocations` ← `payments` |
| Money type not specified | Floating-point errors in balances | Use `DECIMAL(12,2)` (or integer minor units) everywhere, and a single `currency` field |
| Timestamps | Local-time bugs, daylight/offset ambiguity, attendance across midnight | Store **UTC**, convert in the UI; use `DATETIMEOFFSET`/`timestamptz` |
| `attendance` mixes members and trainers | Polymorphic FK, weak integrity | Separate `member_attendance` and `staff_attendance`, or a `person_type` + `CHECK` constraint |
| No schema migration tooling | Two schema files drift; upgrades at client sites break | Adopt **Alembic** (or Flyway) with versioned migrations; the app checks schema version at startup |
| `DataTable` has a delete action | Hard-deleting records with legal/financial weight | Make "delete" an archive action for members, invoices, payments; require a reason and audit it |
| No uniqueness/idempotency on invoices | Double-click or retry creates duplicate invoices | Unique invoice number per branch/year via a sequence; idempotency key on payment creation |
| Indexes only mentioned generally | Slow lists and reports at scale | Index `attendance(member_id, checkin_ts)`, `payments(member_id, paid_at)`, `members(branch_id, status)`, `subscriptions(end_date, status)` |

---

## 4. Medium-Severity Findings and Fixes

### 4.1 Concurrency model details

- **Stale-result race:** If a user types in search and fires worker A then worker B, A can finish after B and overwrite the newer results. Fix: attach a **request token** per screen/query and ignore signals whose token is not the latest, and cancel superseded work where possible.
- **Dead-widget callbacks:** A worker finishing after its screen was destroyed can crash the app. Fix: connect results through the screen's `QObject` context so Qt auto-disconnects, or check an alive flag.
- **`QThread` vs `QRunnable`:** The doc mentions both. Pick one pattern (`QThreadPool` + `QRunnable` is simpler for short tasks) and use it consistently.
- **Connection pool "thread-local cursor":** Pools and thread-locals are different models. Make sure a connection is checked out per unit of work and never held across `await`/signal boundaries.
- **Timeouts:** Every DB and LLM call needs an explicit timeout and a user-visible failure state.

### 4.2 Offline behavior (if you want it)

If front-desk operation must survive network outages, design it deliberately instead of a SQLite fallback:
- Allow only **append-only, conflict-free actions** offline: attendance check-ins and payment *drafts*.
- Queue them locally with a client-generated UUID and timestamp, and sync to the server on reconnect with idempotent inserts.
- Never allow offline edits of member profiles, plan prices, or balances.

### 4.3 Authentication and sessions

- Bcrypt cost 12 is acceptable. Note bcrypt silently truncates input at 72 bytes. Consider **Argon2id** for new deployments.
- Add a password policy (length over complexity), forced change of default admin credentials at first run, and password reset by admin with audit.
- Add **optional MFA (TOTP)** for Admin and Manager roles, since they can see all finances and PII.
- The 30-minute idle timeout should also lock on workstation lock/screensaver and require re-entering the password for sensitive actions (refunds, payroll export, role changes).
- Lockout: 5 failures and 15 minutes is fine. Also add IP/device rate limiting once an API exists, and avoid revealing whether the username or password was wrong.
- Role model: a `role_permissions` table exists, but the matrix is coarse. Move to **permission-based checks** (`member.create`, `invoice.refund`, `payroll.view`) so roles can change without code changes.

### 4.3.1 Inconsistencies inside the document

These do not break the system, but they undermine a document that calls itself "canonical":
- It says **22 services**, but the table lists **15**.
- `invoices`, `meals`, `exercises`, and `role_permissions` appear in tables but not in the ER diagram.
- It says **"Approved & Canonical Reference"** yet contains no change log, owner, or review record.
- §8 lists "Zero Unhandled Syntax Errors" as verification. That is a lint result, not an architectural compliance check.
- The audience line names "Database Administrators", but there is no backup, restore, indexing, or capacity section.

### 4.4 Audit log integrity

"Immutable" needs mechanisms, not a label:
- DB permissions: app account can only `INSERT`.
- Add a **hash chain** (`prev_hash`, `row_hash` over the content and the previous row) so tampering is detectable.
- Log the **before and after values** for financial changes, the actor, the branch, and the client/device ID.
- Ship audit rows to a separate store or write-once location on a schedule.

### 4.5 Attendance and QR security

- Static QR codes can be screenshot and shared. Use **short-lived, signed, rotating tokens** (for example, HMAC with a 30–60 second window) or per-member QR that is validated server-side against active subscription status.
- Anti-passback: reject a second check-in without a check-out within a set window.
- Biometric devices: integrate through the vendor SDK/API, and keep the device on a separate VLAN.
- "Anomaly detection" is listed but not defined. Specify concrete rules first (duplicate check-ins, off-hours entry, expired member entering) before reaching for ML.

---

## 5. Better Architecture Options

Three realistic paths. All three assume you drop silent SQLite failover.

| | **A. Hardened Desktop (minimal change)** | **B. Desktop Client + API Server (recommended)** | **C. Web-first (PWA) + API** |
|---|---|---|---|
| Client | PyQt6/PySide6 as today | PyQt6/PySide6 thin client | React/Next.js responsive web app |
| Data access | Direct to DB | Via **FastAPI** over HTTPS | Via FastAPI over HTTPS |
| Database | MS SQL Server (SQLite only as explicit standalone mode) | **PostgreSQL** | PostgreSQL |
| RBAC and audit | Client-side + DB permissions | **Server-enforced** | Server-enforced |
| Scheduler | DB-locked jobs in clients | Server worker | Server worker |
| Member mobile app | Not possible | Possible later (same API) | Included (PWA) or Flutter later |
| Install/update burden | Per-PC installs | Per-PC installs (client only) | **None** (browser) |
| Rewrite effort | Low | Medium (reuse services as API handlers) | High (new UI) |
| Security posture | Weak-moderate | **Strong** | Strong |
| Best when | One gym, one LAN, a few PCs, tight budget | Multi-branch, growth planned, existing PyQt investment | Many branches, remote managers, member self-service is a priority |

**Recommendation: Option B**, with a path to C. Your services are already stateless and separated, so they convert to API endpoints with relatively little change. The PyQt UI becomes an API client, and you can add a web or mobile member portal later without redoing the backend.

### 5.1 Concrete target stack (Option B)

| Concern | Choice | Reason |
|---|---|---|
| API | **FastAPI** + Pydantic v2 | Python reuse, typed contracts, auto OpenAPI |
| ORM / migrations | **SQLAlchemy 2.x** + **Alembic** | One dialect-neutral layer replaces the regex translator |
| Database | **PostgreSQL** (managed or self-hosted) | No per-core licensing, strong JSON/index support, row-level security available |
| Auth | JWT access token (short) + refresh token, **Argon2id** | Replaces direct-DB sessions; supports MFA later |
| Jobs | APScheduler in a dedicated worker, or **Celery/RQ + Redis** | Single execution, retries, visibility |
| Cache | Redis (only where measured) | Dashboards/KPIs, rate limiting |
| Files | S3-compatible object store or encrypted file share | Photos and documents out of the DB |
| Observability | Structured logging, **Sentry** for crashes, health endpoint | Needed for support across branches |
| Packaging | PyInstaller/Nuitka + signed installer, update channel | Controlled client rollout |
| CI | GitHub Actions: lint, type-check, tests, DB matrix | Prevents regression |

**Licensing note:** PyQt6 is GPL or commercial. If you distribute a proprietary product to customers, you need the commercial license, or you can switch to **PySide6 (LGPL)**, which has a nearly identical API. Check this before shipping to paying customers.

**If you stay on MS SQL Server:** SQL Server Express has a database size cap and limited resources. Check current limits for your version before you rely on it for multi-branch growth.

---

## 6. UI/UX and Accessibility Review

### 6.1 Contrast (measured from the documented tokens)

Calculated using the WCAG relative-luminance formula. The AA minimum is **4.5:1** for normal text and **3:1** for large text and UI components.

| Pair | Ratio | Result |
|---|---:|---|
| Coral `#FA5A3C` on dark canvas `#0C0D0E` | 6.11 | Pass |
| Coral on light canvas `#F4F5F8` | 2.92 | **Fail** (even for large text/UI) |
| Coral on white card `#FFFFFF` | 3.19 | Fail for body text; borderline for large text/UI only |
| White text on a coral button | 3.19 | **Fail** for normal-size button labels |
| Emerald `#10B981` text on white | 2.54 | **Fail** |
| Amber `#F59E0B` text on white | 2.15 | **Fail** |
| Crimson `#EF4444` text on white | 3.76 | Fail for normal text |

**Fixes:**
- Keep the bright tokens for **fills, icons, and charts**, and add **darker "text" variants** for light theme (for example, a coral around `#C93A1E`, emerald around `#047857`, amber around `#B45309`, crimson around `#B91C1C`). Re-measure after choosing, and do not assume.
- For coral buttons in light theme, either use **dark text** on coral or darken the fill until white text reaches 4.5:1.
- Never rely on color alone for status. Pair each status badge with an icon or text label ("Paid", "Pending", "Expired").
- Captions at **10–11px** are too small for comfortable reading. Set a **12px minimum** and support OS font scaling.

### 6.2 Technical accuracy and performance

- "Translucent blur" is misleading. `QGraphicsDropShadowEffect` produces a **shadow**, not a backdrop blur, and Qt widgets do not do real glassmorphism without custom rendering. Reword the doc, or accept a flat "elevated card" design, which is also cheaper to render.
- `QGraphicsEffect` on many cards can slow repaints, especially during sidebar animation and theme switches. Limit shadow effects to a few top-level cards, or pre-render shadows.
- `DataTable` appears built on `QTableWidget`. For large lists use **`QTableView` + a model** (`QAbstractTableModel`) with **server-side pagination and sorting**, rather than loading everything into widgets.
- Add keyboard navigation, visible focus rings, tab order, and screen-reader names for the main flows (check-in, invoice, member search).
- Plan for **localization**: Urdu (RTL) and English, PKR formatting, local date formats, and localized invoices/receipts.

---

## 7. Testing and Verification Upgrades

The current evidence is a lint-style statement plus an automated suite covering auth, member lifecycle, billing, and system health. For a system handling money and PII that is thin.

| Area | Add |
|---|---|
| Billing correctness | Unit and property-based tests (`hypothesis`) for partial payments, discounts, tax rounding, refunds, balance never negative unless intended |
| DB engines | The full suite on every supported engine in CI |
| Security | Tests that RBAC denies each forbidden role/action pair from the matrix; lockout; session timeout; SQL-injection attempts on every search field |
| Concurrency | Tests for stale-result handling, double-submit, two cashiers on the same invoice |
| UI | `pytest-qt` smoke tests for each of the 19 screens in both themes, plus screenshot comparison |
| Load | Representative data volumes (for example, tens of thousands of members and millions of attendance rows) and measured screen load times |
| Migrations | Upgrade tests from the previous schema version with realistic data |
| Backup/restore | A scheduled restore drill, not just a backup job |
| Coverage | Publish a coverage number and set a gate for the billing, auth, and audit modules |

Replace the "Approved & Canonical" status with a **versioned ADR (Architecture Decision Record) log** so changes and reasons are traceable.

---

## 8. Missing Pieces to Add to the Design

1. **Backup and disaster recovery:** automated full + incremental backups, off-site copy, documented RPO/RTO, and restore tests.
2. **Deployment and updates:** signed installers, auto-update channel with rollback, version compatibility check between client and server.
3. **Configuration and secrets:** per-environment config, no secrets in the repo or installer.
4. **Observability:** structured logs with correlation IDs, crash reporting, health checks, and slow-query logging.
5. **Member communications:** expiry and overdue reminders by SMS/WhatsApp/email through a provider abstraction, with opt-out and templates.
6. **Payment integrations:** an abstraction for local payment methods and gateways in addition to cash and card, with reconciliation reports.
7. **Hardware integration:** a defined adapter for turnstiles, biometric readers, and receipt printers.
8. **Membership operations:** freeze/pause, transfer between branches, family/corporate plans, trial passes, referral and promo codes, grace periods.
9. **Reporting:** run heavy analytics on a read replica or materialized views instead of the live transactional tables; schedule report delivery.
10. **Data lifecycle:** retention schedule, archival of old attendance rows, and member data export/erasure.
11. **Documentation hygiene:** change log, owners, and the ADR log noted above.

---

## 9. Prioritized Roadmap

Effort figures are rough estimates for a small team and depend on codebase size, so treat them as planning placeholders, not commitments.

### Phase 0 — Stop the bleeding (about 1–2 weeks)
- [ ] Remove automatic SQLite failover; add explicit Standalone mode and an "Offline: read-only" state
- [ ] Least-privilege DB accounts; `INSERT`-only on audit table
- [ ] Change cascades on financial tables to `RESTRICT`; convert member/invoice/payment deletes to soft delete
- [ ] Add a DB job lock so scheduled jobs run once
- [ ] Move AI key and DB credentials out of plain config
- [ ] Add request tokens to stop stale search/list results
- [ ] Fix contrast failures for status text and light-theme coral

### Phase 1 — Foundation (about 4–8 weeks)
- [ ] Introduce Alembic migrations and a schema version check
- [ ] Add `subscriptions`, `invoice_lines`, `payment_allocations`; adopt `DECIMAL` and UTC timestamps
- [ ] Build the **FastAPI** layer; port services as endpoints; JWT auth with Argon2id
- [ ] Server-side RBAC with permission-based checks; audit written by the server with a hash chain
- [ ] Move the scheduler to a server worker
- [ ] Route AI calls through the server with de-identification, consent, rate limits, and trainer approval
- [ ] CI with both-engine tests (if SQLite Standalone is retained) and the expanded test plan

### Phase 2 — Hardening and growth (about 2–3 months)
- [ ] Encrypt sensitive fields; move photos to protected object storage; retention and erasure workflows
- [ ] Rotating signed QR tokens, anti-passback, hardware adapters
- [ ] MFA for privileged roles; session re-auth for sensitive actions
- [ ] Observability, crash reporting, signed installers with auto-update
- [ ] Backup/restore drills; DR runbook
- [ ] Migrate to PostgreSQL if not already done
- [ ] SMS/WhatsApp reminders and payment gateway abstraction

### Phase 3 — Reach (ongoing)
- [ ] Member web/mobile portal on the same API
- [ ] Read replica or materialized views for analytics
- [ ] Localization (Urdu/RTL), accessibility audit
- [ ] Optional move to a web-first staff client if branch count and remote access demand it

---

## 10. Quick Wins Checklist (do these first)

1. Disable silent SQLite failover.
2. Make audit logs insert-only at the DB permission level.
3. Replace cascade deletes on money tables with `RESTRICT` and add soft delete.
4. Add a job-lock row so scheduled tasks do not run N times.
5. Take the AI API key off the client.
6. Fix status-text contrast and 10px captions.
7. Correct the document: service count (22 vs 15), missing ER entities, the "glass blur" wording, and the "canonical" status.

---

## 11. Assumptions and Limits of This Review

- This is a document review, not a code audit. Findings marked "as described" may already be handled in code.
- Effort estimates are rough and depend on team size and existing code quality.
- Legal and compliance points (personal-data law, licensing terms for PyQt) need confirmation from qualified counsel and the current vendor terms.
- Contrast ratios were computed from the hex values in the document; real rendering (opacity, overlays) may change them.
