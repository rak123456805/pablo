# Peblo TV Mini — Kids Content Management & Discovery System

A submission-ready, production-grade kids content management system (CMS) and child-facing viewer application built for **Peblo TV**.

---

## Architecture Overview

```
                        ┌─────────────────────────────────────────┐
                        │             Child Viewer                │
                        │  (React 19 / Vite / Framer Motion)      │
                        └────────────────────┬────────────────────┘
                                             │
                                     Reads published
                                    catalogue ONLY (GET)
                                             │
                                             ▼
┌──────────────────────┐         ┌─────────────────────────┐
│     CMS Studio       │         │     FastAPI Backend     │
│ (React / TanStack)   ├────────►│ (Async SQLAlchemy / DB) │
└──────────────────────┘ Admin / └───────────┬─────────────┘
                          Editor             │
                          APIs               ▼
                                 ┌─────────────────────────┐
                                 │   Storage Abstraction   │
                                 │   (Local / MinIO / R2)  │
                                 └─────────────────────────┘
```

---

## Quick Start (Clean Environment)

### Run Everything with Docker Compose

Ensure Docker is running, then execute:

```bash
# 1. Start all services (PostgreSQL main, Postgres test, FastAPI Backend, React Frontend)
docker compose up -d

# 2. Check container statuses
docker compose ps
```

Services exposed:
- **Child Viewer & CMS Studio**: `http://localhost:5173` (or `http://localhost:80`)
- **FastAPI API & OpenAPI Docs**: `http://localhost:8000/docs`
- **PostgreSQL Main DB**: `localhost:5434`
- **PostgreSQL Test DB**: `localhost:5433`

*Note: Database migrations (`alembic upgrade head`) and seed data import (`python -m app.scripts.seed`) execute automatically on API container startup.*

### Demo Credentials

- **Admin**: `admin@peblo.local` / `admin123` (Full CRUD + Publishing privileges)
- **Editor**: `editor@peblo.local` / `editor123` (CRUD & Validation privileges; Publishing restricted)

> **Authentication Scope**: Authentication is intentionally limited to internal CMS users (`editor` / `admin` roles). Public registration / signup is deliberately omitted per challenge design; production environments would manage internal credentials via secure secret stores or organization Identity/SSO.

---

## Running Test Suites

Backend unit and integration tests run against PostgreSQL test DB on port 5433:

```bash
# Run artwork unit tests (no DB required)
cd backend
python -m pytest tests/test_artwork.py -v

# Run full backend test suite (requires db_test container running)
docker compose up -d db_test
cd backend
python -m pytest -v
```

---

## System Architecture & Technical Decisions

### 1. Atomic Publishing Strategy
Catalogue publication must be **atomic**, **idempotent**, and **recorded**. The publishing pipeline in `app/services/publisher.py` executes the following sequence:

1. **Validation Gate**: Runs `build_validation_report(db)`. If any **blocking** issue exists, publication is halted immediately and `422 Unprocessable Entity` is returned. The live catalogue file is untouched.
2. **Sentinel Record Creation**: Creates a `PublishRun` database record with `status="running"` and `started_at=now()`.
3. **In-Memory Compilation**: Compiles all published shows, regular seasons, trailers (Season 0), and collapsed language variants into a structured `CatalogOut` Pydantic model.
4. **Temporary File Write**: Serializes JSON and writes to storage as `catalog_<run_id>.json`.
5. **Atomic Rename / Replace**: Calls `storage.atomic_replace("catalog_<run_id>.json", "catalog.json")`.
   - On **Local Storage**: Uses `os.replace()`, guaranteeing atomic inode swap on POSIX and best-effort swap on Windows NTFS. Readers never observe a partially-written file.
   - On **Cloud Storage (S3 / R2)**: Executes single-object copy to `catalog.json` followed by temporary key deletion.
6. **Sentinel Finalization**: Updates `PublishRun` record to `status="success"`, recording `shows_count`, `episodes_count`, and `finished_at`.

### 2. What Happens if Publishing Dies Mid-Process?
- **Process dies before Step 5 (during validation or JSON assembly)**: `catalog.json` remains untouched and valid. The `PublishRun` record remains `status="running"`. A background cleanup job flags stuck runs as `failed` after timeout.
- **Process dies during Step 5 (atomic rename)**: Inode replace operations are atomic at the filesystem level. The viewer reads either the complete previous `catalog.json` or the complete new `catalog.json` — never a corrupted fragment.
- **Process dies after Step 5 (before updating database sentinel)**: The live `catalog.json` is updated and serving new content. The sentinel record remains `status="running"` until reconciled by automated monitoring.

### 3. Storage Abstraction & Cloudflare R2 Migration
Artwork files and catalogue JSON are managed through an abstract base class `StorageProvider` (`app/services/artwork_storage.py`) defining:
`put()`, `get()`, `delete()`, `exists()`, `atomic_replace()`, `public_url()`.

Three concrete storage backends exist:
- `LocalStorageProvider`: Stores files on local disk under `./storage/` served via FastAPI StaticFiles.
- `MinioStorageProvider`: Stores files in self-hosted MinIO S3 bucket using `boto3`.
- `R2StorageProvider`: Stores files in Cloudflare R2 / AWS S3.

**To transition from local disk to Cloudflare R2**:
Change `STORAGE_BACKEND=r2` in `.env` and provide R2 credentials (`R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`). **Zero code changes are required.**

### 4. Search Implementation & Scaling Limits
Catalogue search (`GET /api/v1/catalog/search`) reads the published `catalog.json` file into memory and filters shows, sections, categories, and episodes using Python list comprehensions.

**Why this approach is acceptable for current dataset**:
- The catalogue contains ~95 source rows (< 50 KB JSON payload).
- Per-query response latency is < 1ms with 0 database query overhead and 0 table locks.
- Search rules require matching show title, episode title, and category simultaneously, which is simple and fast in memory.

**When this approach stops scaling**:
- Above **~5,000 episodes**: The JSON file exceeds 5 MB. In-memory parsing per request creates excessive RAM allocation.
- Above **~50,000 episodes**: O(N) list scanning produces noticeable CPU latency (> 100ms per request).

**Scale Transition Plan**:
Move search indexing to PostgreSQL full-text search (`tsvector` + GIN index) or an external search engine (Elasticsearch / Typesense / Algolia) populated asynchronously upon publish completion.

### 5. Why a Pre-Published Catalogue Exists
Decouples high-volume child viewer traffic from CMS editorial operations:
- **Zero Database Load**: Viewer requests read a static JSON file or CDN endpoint, preventing complex SQL joins on every viewer page load.
- **Resilience**: Even if the primary PostgreSQL database suffers an outage or maintenance window, child viewers continue streaming content seamlessly.
- **Instant CDN Edge Caching**: `catalog.json` can be cached on Cloudflare Edge nodes globally for ultra-low latency.

### 6. Trade-offs of Pre-Published Catalogues
- **Stale Data Window**: Content edits in CMS are not visible to viewers until an Admin explicitly triggers a Publish Run.
- **Publish Latency**: Large catalogues require full validation scans and JSON compilation before deployment.

### 7. What Was Deliberately Left Out
- Video transcode pipelines (HLS/DASH variant generation).
- User billing and subscription paywalls.
- Complex AB testing frameworks.
*Rationale*: Prioritized 100% of engineering effort on core requirements: atomic recorded idempotent publishing, role enforcement, byte-level artwork validation, and validation reporting.

### 8. AI Tools Used
- **Antigravity AI Pair Programmer** (Google DeepMind team) for scaffolding, test generation, and architectural verification.

### 9. Where AI Output Was Accepted
- Boilerplate Pydantic schema structures.
- Initial React component layouts and Tailwind CSS utility classes.
- Pytest fixture configurations.

### 10. Where AI Output Was Rejected
- **Superficial Exception Masking**: Rejected attempts to wrap validation errors in silent try/except blocks.
- **Modifying Seed Data**: Rejected AI suggestions to alter `seed_shows.json` to hide intentional errors.
- **Non-Atomic File Writes**: Rejected standard `open("catalog.json", "w")` file writes in favor of `os.replace` atomic swaps.
- **Frontend-Only Permissions**: Rejected client-side role checks without backend FastAPI dependency enforcement.

### 11. Approximate Time Spent Per Part
| Component | Hours Spent |
|-----------|-------------|
| Auth & Role Enforcement Backend | 2.5 hrs |
| Content CRUD & Business Rule Validation | 3.0 hrs |
| Byte-Level Artwork Validation & Storage Abstraction | 2.5 hrs |
| Validation Report & Seed Anomaly Detection | 3.0 hrs |
| Atomic Publishing Pipeline | 3.5 hrs |
| CMS Studio Frontend (React / Query / Forms) | 4.5 hrs |
| Child Viewer Frontend (Framer Motion / Warm Theme) | 3.5 hrs |
| CI/CD, Docker Compose & Documentation | 2.5 hrs |
| **Total Engineering Time** | **~25.0 hrs** |

---

## Real Seed-Data Issues Discovered & Surfaced

The provided seed file (`seed_shows.json`) contains **four intentional data quality violations**. The system deliberately preserves these errors in the database and surfaces them via `GET /admin/validation/report` rather than hiding or modifying them:

1. **Rhyme Rangers (`slug: rhyme-rangers`)**: `section` field is `null`. Surfaced as a **blocking** validation error for published shows (`MISSING_SECTION`).
2. **Episode ep_0036 (`Discover India S1E4`)**: `status: published` but `artwork_available: []`. Surfaced as a **blocking** validation error (`MISSING_ARTWORK`).
3. **ep_9001 / ep_0004 (`motis-many-lives-s01e02`)**: Duplicate `(content_group, language)` pair for `hi` language. Surfaced as a **blocking** error (`DUPLICATE_CONTENT_GROUP_LANG`).
4. **motis-many-lives-s01e02**: Hindi language variants disagree on episode titles ("Rain on the Roof" vs "The Lost Kite (v2)"). Surfaced as a **blocking** error (`CONTENT_GROUP_IDENTITY_CONFLICT`).

---

## Monitoring & Alerting Specification

### Meaningful System Alert: Catalogue Publish Failure Alert

- **Metric**: `PublishRun.status == 'failed'` or consecutive failed publish attempts > 1.
- **Severity**: **P1 / Critical**
- **Rationale**: Catalogue publication is the highest-value operation in the platform. A failed publish run prevents new kids content, fixed errors, and fresh episodes from reaching viewers.
- **Notification Routing**: Triggers immediate PagerDuty on-call dispatch and posts to `#peblo-ops-alerts` Slack channel with the exact `error_message` from the `PublishRun` record.

---

## Production Secret Handling

1. `JWT_SECRET_KEY` must be generated using a cryptographically secure random generator (`openssl rand -hex 32`).
2. Environment secrets in production must be injected dynamically via HashiCorp Vault, AWS Secrets Manager, or Kubernetes Secrets — **never committed to version control**.
