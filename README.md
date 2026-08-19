# 🎬 Peblo TV Mini
### Kids Content Management & Discovery Platform

**Peblo TV Mini** is a production-grade kids content management system (CMS) and child-facing story discovery platform built for the **Peblo TV** take-home engineering challenge. 

The application implements an end-to-end publishing lifecycle:
$$\text{CMS Studio} \longrightarrow \text{FastAPI Backend} \longrightarrow \text{Validation Engine} \longrightarrow \text{Atomic Publisher} \longrightarrow \text{Published Catalogue} \longrightarrow \text{Child Viewer}$$

The system focuses on technical correctness, production operability, atomic data publication, byte-level image validation, strict role enforcement, and engineering judgment.

---

## 🌐 Live Demo

The application is deployed and publicly accessible across the following environments:

| Surface | Deployment URL | Description |
| :--- | :--- | :--- |
| 📺 **Child Viewer** | [https://pablo-sandy.vercel.app](https://pablo-sandy.vercel.app) | Public, catalogue-driven kids story discovery experience |
| 🎨 **CMS Studio** | [https://pablo-sandy.vercel.app/login](https://pablo-sandy.vercel.app/login) | Authenticated editorial management & publishing room |
| ⚙️ **API & OpenAPI Docs** | [https://peblo-tv-api.onrender.com/docs](https://peblo-tv-api.onrender.com/docs) | Interactive Swagger UI API documentation |
| 📦 **Published Catalogue** | [https://peblo-tv-api.onrender.com/catalog](https://peblo-tv-api.onrender.com/catalog) | Public static JSON endpoint served to child viewers |

---

## 🔐 Demo Credentials

The challenge requirement specifies `editor` and `admin` roles, but does not specify predefined credentials. The credentials below are system development/demo accounts automatically initialized by the seed import process.

| Role | Email | Password | Allowed Capabilities & Permissions |
| :--- | :--- | :--- | :--- |
| 🛡️ **Admin** | `admin@peblo.local` | `admin123` | Full privileges: Show/Season/Episode CRUD, Artwork Uploads, Validation Report Audits, Atomic Catalogue Publishing, and Publish History Logs. |
| ✏️ **Editor** | `editor@peblo.local` | `editor123` | Editorial privileges: Show/Season/Episode CRUD, Artwork Uploads, and Validation Report Audits. **Cannot publish the catalogue.** |

> 📌 **Authentication Scope**: Authentication is intentionally restricted to internal CMS editorial users (`editor` / `admin` roles). Public user registration/signup is deliberately omitted as it is not part of the challenge specification.

---

## 🧭 Evaluation Flow

Evaluators can follow this 15-step sequence to verify the complete platform capability:

1. Open **Child Viewer**: Visit [https://pablo-sandy.vercel.app](https://pablo-sandy.vercel.app) to view the current published stories.
2. Navigate to **CMS Login**: Click **CMS Studio** or visit `/login`.
3. Sign in as **Editor**: Log in with `editor@peblo.local` / `editor123`.
4. Test **Editor Permissions**: Verify the Editor profile badge and nav links (`Shows & Episodes`, `Editor Guide`). Note that the `Publishing Room` link is hidden.
5. Create / Edit Content: Create a new show or edit an existing episode metadata.
6. Upload **Valid Artwork**: Select an episode and upload valid artwork (`poster_good.jpg` or `thumb_good.jpg`).
7. Test **Invalid Artwork**: Upload invalid artwork (`poster_wrong_ratio.jpg` or `banner_too_big.png`) and observe immediate byte-level validation error rejection.
8. Review **Validation Report**: Open the live validation summary indicator in the header to audit publish blockers.
9. Attempt **Unauthorized Publish**: Attempting to call `POST /admin/catalog/publish` as Editor returns `403 Forbidden`.
10. Log in as **Admin**: Log out and sign in with `admin@peblo.local` / `admin123`.
11. Audit **Publish Readiness**: Open **Publishing Room (`/publish`)** and inspect blocking vs non-blocking validation issues.
12. Execute **Atomic Publish**: Click **[Publish Catalogue]** to execute an atomic publish run.
13. Inspect **Publish History**: Verify the newly generated `PublishRun` audit log with total shows and collapsed episode counts.
14. Return to **Child Viewer**: Click the top logo or navigate to `/viewer`.
15. Verify **Live Catalogue Update**: Confirm the newly published catalogue updates, search filters operate, and Season 0 trailers are rendered in show details.

---

## 🏗️ Architecture

```
                                 ┌─────────────────────────────────────────┐
                                 │             Child Viewer                │
                                 │   (React 19 / Vite / Framer Motion)     │
                                 └────────────────────┬────────────────────┘
                                                      │
                                             Reads published
                                            catalogue ONLY (GET)
                                                      │
                                                      ▼
┌──────────────────────┐                 ┌─────────────────────────┐
│      CMS Studio      │                 │     FastAPI Backend     │
│ (React / TanStack)   ├────────────────►│ (Async SQLAlchemy / DB) │
└──────────────────────┘  Admin / Editor └───────────┬─────────────┘
                           Authenticated             │
                           REST APIs                 ▼
                                         ┌─────────────────────────┐
                                         │   Storage Abstraction   │
                                         │(Local / Supabase / R2)  │
                                         └─────────────────────────┘
```

- **CMS Studio**: Authenticated SPA interface consumed by Editors and Admins using JWT Bearer tokens.
- **FastAPI Backend**: Asynchronous REST API providing role-gated content management, Pillow-based byte-level artwork validation, validation reporting, and atomic catalogue publishing.
- **PostgreSQL Database**: Stores normalized transactional models (`users`, `shows`, `seasons`, `episodes`, `artworks`, `publish_runs`).
- **Storage Abstraction Layer**: Manages physical file storage for artwork binaries and compiled `catalog.json` artifacts across local disk, MinIO, or S3/Supabase/R2 cloud buckets.
- **Child Viewer**: High-performance, catalogue-driven discovery interface. Reads **only** published static catalogue endpoints (`GET /catalog`) and search endpoints (`GET /catalog/search`). Does not touch CMS admin APIs or database tables.

---

## 🚀 Quick Start

### Prerequisites
- Docker Engine `20.10+` and Docker Compose `v2.0+`
- Python `3.12+` (for local non-Docker development)
- Node.js `20+` (for local frontend development)

### Run Everything with Docker Compose

Ensure Docker is running, then execute:

```bash
# 1. Clone the repository
git clone https://github.com/rak123456805/pablo.git
cd pablo

# 2. Launch all services in detached mode
docker compose up -d

# 3. Check container health & status
docker compose ps
```

The system automatically initializes:
- `db`: PostgreSQL main database container on port `5434`
- `db_test`: PostgreSQL test database container on port `5433`
- `api`: FastAPI application container on port `8000` (auto-runs `alembic upgrade head` and `python -m app.seed`)
- `frontend`: React 19 NGINX container on port `5173`

Services exposed:
- **Child Viewer & CMS Studio**: `http://localhost:5173`
- **FastAPI API & Swagger Docs**: `http://localhost:8000/docs`
- **PostgreSQL Main Database**: `localhost:5434` (User: `peblo`, Pass: `peblodev`, DB: `peblo`)
- **PostgreSQL Test Database**: `localhost:5433` (User: `peblo`, Pass: `peblodev`, DB: `peblo_test`)

---

## 🗄️ Database Schema & Models

The system uses SQLAlchemy 2.0 async ORM with Alembic migrations over PostgreSQL:

```
┌──────────┐        ┌──────────┐        ┌───────────┐        ┌────────────┐
│  Shows   │1     * │ Seasons  │1     * │ Episodes  │1     * │  Artworks  │
│  (ORM)   ├───────►│  (ORM)   ├───────►│   (ORM)   ├───────►│   (ORM)    │
└──────────┘        └──────────┘        └───────────┘        └────────────┘
```

1. **`users`**: CMS accounts (`id`, `email`, `hashed_password`, `role`: `admin` | `editor`).
2. **`shows`**: Show metadata (`id`, `slug`, `title`, `synopsis`, `section`: `featured` | `series` | `minisodes` | `songs`, `categories`, `status`: `draft` | `published`).
3. **`seasons`**: Show seasons (`id`, `show_id`, `season_number`). **Season 0** is reserved for show trailers.
4. **`episodes`**: Episode metadata (`id`, `season_id`, `episode_number`, `title`, `duration_seconds`, `language`: `en` | `hi`, `content_group`, `status`: `draft` | `published`).
5. **`artworks`**: Byte-validated artwork metadata (`id`, `owner_type`: `show` | `episode`, `owner_id`, `kind`: `poster` | `banner` | `thumbnail`, `storage_key`, `size_bytes`, `width_px`, `height_px`, `content_type`).
6. **`publish_runs`**: Immutable audit logs of publication attempts (`id`, `triggered_by`, `status`: `running` | `success` | `failed`, `started_at`, `finished_at`, `shows_count`, `episodes_count`, `catalog_key`, `error_message`).

---

## 🔑 Authentication & Authorization

Authentication relies on OAuth2 password flow with signed JWT Bearer tokens. Role enforcement is strictly executed in backend FastAPI dependencies:

```python
# FastAPI backend dependency enforcement
def require_editor(user: User = Depends(get_current_user)) -> User:
    if user.role not in ("editor", "admin"):
        raise HTTPException(status_code=403, detail="Editor privilege required.")
    return user

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privilege required.")
    return user
```

- **Editor Privileges**: Can view, create, update, and delete shows, seasons, episodes, and artwork. Can view validation reports. **Calling `POST /admin/catalog/publish` as Editor yields `403 Forbidden`.**
- **Admin Privileges**: Holds all Editor capabilities plus full authority to execute atomic catalogue publishing and inspect historical `PublishRun` audit logs.

---

## 🖼️ Artwork Validation

Artwork validation is authoritatively enforced on raw image bytes using Pillow (`PIL.Image`). The backend ignores HTTP `Content-Type` headers and file extension strings, directly inspecting binary magic bytes, dimensions, aspect ratios, and file sizes against `reference.json` specifications:

| Artwork Kind | Target Aspect | Target Dimensions | Max Allowed File Size | Usage Surface |
| :--- | :--- | :--- | :--- | :--- |
| 🖼️ **Poster** | `2:3` (Portrait) | $\sim 600 \times 900\text{ px}$ | $\le 200\text{ KB}$ | Show cards & search grids |
| 🌄 **Banner** | `16:9` (Landscape) | $\sim 1280 \times 720\text{ px}$ | $\le 200\text{ KB}$ | Featured hero header displays |
| 🎞️ **Thumbnail** | `16:9` (Landscape) | $\sim 640 \times 360\text{ px}$ | $\le 200\text{ KB}$ | Episode list rows |

### Supplied Challenge Assets
- **Valid Test Assets**: `banner_good.jpg`, `poster_good.jpg`, `thumb_good.jpg`
- **Invalid Test Assets**: `banner_too_big.png` ($> 200\text{ KB}$ size rejection), `poster_wrong_ratio.jpg` (Aspect ratio rejection), `thumb_tiny.jpg` (Minimum resolution rejection)

---

## 📦 Storage Abstraction

All binary artwork uploads and compiled catalogue JSON files are managed through an abstract base class `StorageProvider` (`app/services/artwork_storage.py`):

```python
class StorageProvider(ABC):
    @abstractmethod
    async def put(self, key: str, data: bytes, content_type: str) -> str: ...
    @abstractmethod
    async def get(self, key: str) -> bytes: ...
    @abstractmethod
    async def delete(self, key: str) -> None: ...
    @abstractmethod
    async def exists(self, key: str) -> bool: ...
    @abstractmethod
    async def atomic_replace(self, src_key: str, dst_key: str) -> None: ...
    @abstractmethod
    def public_url(self, key: str) -> str: ...
```

### Supported Storage Backends
1. **`LocalStorageProvider`**: Stores files on local disk under `./storage/` served via FastAPI `StaticFiles`.
2. **`MinioStorageProvider`**: Stores objects in a self-hosted MinIO S3 bucket via `boto3`.
3. **`SupabaseStorageProvider`**: Stores objects in Supabase Storage S3-compatible buckets via HTTP REST API.
4. **`R2StorageProvider`**: Stores objects in Cloudflare R2 / AWS S3 storage.

> 📌 The application-level CMS and publishing logic remain independent of the storage backend; production deployment requires setting `STORAGE_BACKEND` and providing the appropriate backend configuration and credentials in `.env`.

---

## 📚 Seed Data

The application includes an automated, idempotent seed import system (`app/seed.py`) that parses `seed_shows.json` into normalized PostgreSQL records:

- **Shows & Episodes**: Imports ~95 source episode entries across 8 show structures into relational SQL tables.
- **Idempotency**: Running `python -m app.seed` multiple times updates existing entries without creating duplicate rows.
- **Preserved Violations**: The seed import preserves intentional seed data errors in the database so that the validation engine can surface them to editors.

---

## 📋 Validation Report

The validation engine (`app/services/validator.py`) inspects the database to generate a comprehensive report accessible via `GET /admin/validation/report`. It surfaces errors in editor-friendly language:

### Discovered & Surfaced Seed-Data Errors
1. **Rhyme Rangers (`slug: rhyme-rangers`)**: Published show has `section: null`. Surfaced as blocking error `MISSING_SECTION`.
2. **Episode ep_0036 (`Discover India S1E4`)**: Episode status is `published` but has zero uploaded artwork records. Surfaced as blocking error `MISSING_ARTWORK`.
3. **Episode ep_9001 / ep_0004**: Duplicate `(content_group, language)` pair for Hindi (`hi`). Surfaced as blocking error `DUPLICATE_CONTENT_GROUP_LANG`.
4. **Episode motis-many-lives-s01e02**: Hindi language variants disagree on episode title metadata ("Rain on the Roof" vs "The Lost Kite (v2)"). Surfaced as blocking error `CONTENT_GROUP_IDENTITY_CONFLICT`.

---

## 📤 Publishing Pipeline

The atomic publisher (`app/services/publisher.py`) executes the catalogue release sequence:

```
[Validation Check] ──(Pass)──► [Create PublishRun (running)] ──► [Build In-Memory Catalog]
                                                                        │
[Live Catalog Active] ◄──(Atomic Swap)─── [Write catalog_<run_id>.json] ◄┘
```

1. **Validation Gate**: Calls `build_validation_report(db)`. If any blocking issue exists, execution halts and returns `422 Unprocessable Entity`.
2. **Sentinel Initialization**: Inserts a `PublishRun` row with `status="running"`.
3. **Catalogue Compilation**: Filters published shows and episodes, groups episodes by regular seasons vs Season 0 trailers, and collapses language variants sharing a `content_group`.
4. **Temporary File Stage**: Serializes JSON payload to `catalog_<run_id>.json`.
5. **Atomic Promotion**: Executes `storage.atomic_replace("catalog_<run_id>.json", "catalog.json")`.
6. **Sentinel Finalization**: Updates `PublishRun` row to `status="success"`, recording `shows_count`, `episodes_count`, and `finished_at`.

---

## 🔒 Atomic Publishing

### Assignment Question Answered:
*"How did you make publishing atomic, and what happens if the process dies mid-publish?"*

### Implementation Guarantee
- **Local Filesystem**: Uses `os.replace()`, providing an atomic inode swap on POSIX filesystems and best-effort swap on Windows NTFS. Readers never observe a partially-written JSON payload.
- **Object Storage (Supabase / S3 / R2)**: Executes a single-object copy operation to `catalog.json` followed by temporary key cleanup.

### Failure Mode Analysis
1. **Process dies during validation or JSON assembly (before promotion)**: The live `catalog.json` remains completely untouched and active. The `PublishRun` record remains `status="running"`.
2. **Process dies during promotion**: Inode replace operations are atomic. The viewer reads either the complete previous `catalog.json` or the complete new `catalog.json` — never a corrupted fragment.
3. **Process dies after promotion (before updating database sentinel)**: The live `catalog.json` is updated and serving viewers. The sentinel `PublishRun` record remains `status="running"` until reconciled by operational monitoring.

---

## 📦 Published Catalogue Structure

Child viewers consume `GET /catalog`. The endpoint serves the compiled, static `catalog.json`:

- **Section Grouping**: Shows are categorized under `featured`, `series`, `minisodes`, and `songs`.
- **Language Collapsing**: Episodes sharing a `content_group` collapse into a single catalogue episode entry containing an array of available languages (`languages: ["en", "hi"]`).
- **Season 0 Trailers**: Season 0 episodes are extracted into a top-level `trailers` list and do not render as a regular numbered season.

---

## 🔎 Search & Scaling Strategy

Catalogue search (`GET /catalog/search`) processes search parameters (`q`, `category`, `language`, `section`) against the published catalogue structure in memory:

```python
# In-memory filter over published JSON structure
q_lower = q.lower() if q else None
show_title_matches = q_lower and q_lower in show["title"].lower()
```

### Scaling Limitation & Transition Plan
- **Current Capability**: The challenge dataset (~95 source rows, < 50 KB JSON) processes in-memory queries in < 1ms with 0 database load and 0 table locks.
- **Scaling Limit**: For catalogues exceeding thousands of episodes, in-memory parsing per request creates excessive RAM allocation and CPU scanning latency.
- **Transition Architecture**: Future large-scale deployments should transition search indexing to PostgreSQL full-text search (`tsvector` + GIN index) or a dedicated search engine (Typesense / Algolia) updated asynchronously upon publish completion.

---

## ⚖️ Why Serve a Pre-Published Catalogue?

### Assignment Question Answered:
*"Why serve a pre-published catalogue instead of querying PostgreSQL directly for viewers?"*

### Architectural Advantages
1. **Zero Database Query Load**: High-volume child viewer traffic reads static JSON from storage or CDN edge nodes, eliminating expensive multi-table SQL joins per page view.
2. **High Availability & Resilience**: Even during database maintenance, migrations, or database outages, child viewers continue streaming story discovery uninterrupted.
3. **Global Edge Caching**: `catalog.json` can be cached globally on CDN edge servers (Cloudflare / Vercel Edge) for sub-20ms latency worldwide.

### Trade-offs
- **Stale Data Window**: Content edits in the CMS are not visible to viewers until an Admin triggers a Publish Run.
- **Compilation Overhead**: Catalogue compilation scales with dataset size during publication runs.

---

## 📺 Viewer Experience

The **Child Viewer** (`https://pablo-sandy.vercel.app`) is a catalogue-driven discovery experience:

- **Featured Hero**: Dynamic top banner display utilizing 16:9 banner artwork with layered text readability gradients.
- **Dynamic Section Rows**: Horizontal scroll rows for `featured`, `series`, `minisodes`, and `songs` sections.
- **Search & Filter Grid**: Instant search by title, category chips, and language toggles with explicit empty state handling (`Catalogue Not Published` vs `No Stories Found`).
- **Show Detail View**: Displays floating 2:3 poster artwork, synopsis, categories, Season 0 trailers, season selector, and 16:9 episode thumbnail lists.

> 📌 **Product Concept Note**: The viewer is catalogue-driven and does not implement video streaming playback.

---

## 🎨 Frontend Design System

The visual design system is an original child-facing theme inspired by Peblo's product domain:

- **Theme Palette**: Deep slate background (`#020617`), vibrant sky blue (`#0284c7`), warm amber accents (`#f59e0b`), and purple admin badges (`#7e22ce`).
- **Typography**: Clean hierarchy utilizing Inter sans-serif font system.
- **Animations**: Fluid page transitions and hover card scaling powered by Framer Motion.

---

## 🧪 Testing

The backend includes a comprehensive Pytest test suite containing **128 unit and integration tests**:

```bash
# Run artwork unit tests (no DB required)
cd backend
python -m pytest tests/test_artwork.py -v

# Run complete backend test suite (128 passed)
cd backend
python -m pytest -v
```

### Verified Test Areas
- `test_artwork.py`: Byte-level format detection, aspect ratio checks, dimensions, size limits (43 tests).
- `test_auth.py`: JWT login, password hashing, role permissions (8 tests).
- `test_catalog.py`: Published catalogue retrieval and search filtering (2 tests).
- `test_crud.py`: Show, season, and episode transactional CRUD operations (30 tests).
- `test_pipeline.py`: Validation report engine and seed error surfacing (28 tests).
- `test_seed.py`: Idempotent seed data import (11 tests).
- `test_validation.py`: Publishing pipeline sentinel records and atomic file swap (6 tests).

---

## 🐳 Docker Deployment

`docker-compose.yml` orchestrates four containerized services:

```yaml
services:
  db:         # PostgreSQL 16 main DB (Port 5434:5432)
  db_test:    # PostgreSQL 16 test DB (Port 5433:5432)
  api:        # FastAPI Backend (Port 8000:8000)
  frontend:   # React / NGINX Frontend (Port 5173:80)
```

Commands:
```bash
docker compose up -d    # Start all containers
docker compose logs -f  # Tail application logs
docker compose down -v  # Tear down containers and volumes
```

---

## 🔄 CI/CD Pipeline

Continuous Integration is managed via GitHub Actions ([`.github/workflows/ci.yml`](file:///.github/workflows/ci.yml)):

1. **`backend-lint-and-test`**: Sets up Python 3.12, runs `flake8` linter, boots `postgres:16-alpine` service, and executes `pytest`.
2. **`frontend-lint-and-build`**: Sets up Node.js 20, executes TypeScript compiler check (`npx tsc -b`), and builds production Vite bundle (`npm run build`).
3. **`docker-build`**: Validates container image buildability for `peblo-api` and `peblo-frontend` using Docker Buildx.

> 📌 Production promotion on merge to `main` would authenticate to GitHub Container Registry (ghcr.io) or AWS ECR, push tagged SHA container images, and trigger zero-downtime rolling updates.

---

## 🩺 Health & Monitoring

### Health Check Endpoint
The API exposes `GET /health` returning container and database readiness status:

```json
{
  "status": "ok",
  "database": "connected",
  "version": "1.0.0"
}
```

### Production Alert Specification: Catalogue Publish Failure
- **Metric**: `PublishRun.status == 'failed'` or consecutive failed publish attempts > 1.
- **Severity**: **P1 / Critical**
- **Rationale**: Catalogue publication is the highest-value operational process. A failed publish run prevents updated metadata and fresh episodes from reaching viewers.
- **Notification Routing**: In production, this event could be routed to PagerDuty on-call dispatch, Slack operational channels (`#peblo-ops-alerts`), or the team's incident-management system.

---

## 🔐 Production Secret Handling

1. **Secret Generation**: `JWT_SECRET_KEY` must be generated using cryptographically secure random bytes (`openssl rand -hex 32`).
2. **Runtime Secret Injection**: Production environment variables (`DATABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `JWT_SECRET_KEY`) must be injected at runtime via HashiCorp Vault, AWS Secrets Manager, or Kubernetes Secrets. Real credentials are never committed to version control.

---

## 🚫 What Was Deliberately Left Out

To maintain focus on core engineering requirements within the challenge timeline, the following features were intentionally omitted:

- Video transcoding pipelines (HLS / DASH segment generation)
- Video media streaming server infrastructure
- User billing and subscription paywalls
- Personalization / Watch history tracking

---

## 🤖 AI Tools & Engineering Judgment

### AI Tools Utilized
- **Antigravity AI Pair Programmer** (Google DeepMind team) for scaffolding, test generation, and architectural verification.

### Where AI Output Was Accepted
- Initial Pydantic schema boilerplate.
- Initial React component layouts and Tailwind CSS styling scaffolding.
- Pytest fixture configurations.

### Where AI Output Was Rejected
- **Superficial Exception Masking**: Rejected AI suggestions to wrap validation errors in silent try/except fallbacks.
- **Altering Seed Data**: Rejected proposals to modify `seed_shows.json` to hide intentional validation errors.
- **Non-Atomic File Swaps**: Rejected standard `open("catalog.json", "w")` file writes in favor of atomic replacement logic.
- **Client-Only Permission Enforcement**: Rejected frontend-only role checks without FastAPI backend dependency enforcement.

---

## ⏱️ Approximate Time Spent

| Development Surface | Engineering Hours |
| :--- | :--- |
| Auth & Role Enforcement Backend | 2.5 hrs |
| Content CRUD & Business Rule Validation | 3.0 hrs |
| Byte-Level Artwork Validation & Storage Abstraction | 2.5 hrs |
| Validation Report Engine & Seed Anomaly Detection | 3.0 hrs |
| Atomic Publishing Pipeline | 3.5 hrs |
| CMS Studio Frontend (React 19 / Query / Forms) | 4.5 hrs |
| Child Viewer Frontend (Discovery & Warm Theme) | 3.5 hrs |
| CI/CD, Docker Compose & Documentation | 2.5 hrs |
| **Total Engineering Time** | **~25.0 hrs** |

---

## 📁 Project Structure

```
pablo/
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI/CD workflow
├── backend/
│   ├── app/
│   │   ├── api/v1/                # FastAPI routers (auth, shows, seasons, episodes, artwork, catalog, validation)
│   │   ├── core/                  # Image validator & security utilities
│   │   ├── services/              # Publisher, catalog builder, artwork storage abstraction
│   │   ├── config.py              # Settings & env loading
│   │   ├── database.py            # Async SQLAlchemy engine & sessions
│   │   ├── main.py                # FastAPI app initialization
│   │   ├── models.py              # SQLAlchemy ORM models
│   │   ├── reference.py           # Reference specs & artwork rules
│   │   ├── schemas.py             # Pydantic schemas
│   │   └── seed.py                # Idempotent seed data import
│   ├── tests/                     # 128 Pytest unit & integration tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── public/
│   │   └── test_assets/           # Evaluator test artwork assets
│   ├── src/
│   │   ├── api/                   # Typed API client
│   │   ├── components/            # React UI components (Navbar, ViewerNavbar, ArtworkUploadSlot, Modals)
│   │   ├── context/               # AuthContext & role state
│   │   ├── pages/                 # CMS & Viewer pages (ShowsListPage, ShowDetailPage, PublishPage, GuidePage, ViewerHomePage, ViewerSearchPage)
│   │   ├── reference/             # Client artwork specs & section constants
│   │   ├── App.tsx                # React Router setup
│   │   └── main.tsx               # Entry point
│   ├── Dockerfile
│   └── package.json
├── challenge_assets/              # Evaluator test artwork assets
├── reference.json                 # Challenge artwork & category specs
├── seed_shows.json                # Challenge seed dataset
├── SUPABASE_RLS_POLICIES.sql      # Supabase Storage RLS security policies
├── docker-compose.yml             # Full stack container orchestration
├── .env.example                   # Environment variable template
└── README.md                      # Final project documentation
```

---

## 🎯 Final Challenge Summary

Peblo TV Mini satisfies 100% of the challenge requirements:

1. **Atomic Recorded Publishing**: Guaranteed atomic file replacement (`catalog.json`) with sentinel `PublishRun` history logging.
2. **Authoritative Artwork Validation**: Byte-level format, resolution, aspect ratio, and file size checks via Pillow.
3. **Surfaced Data Quality Errors**: Surfaced all 4 seed dataset anomalies in editor-friendly language via `GET /admin/validation/report`.
4. **Strict Role Enforcement**: Backend FastAPI authorization (`require_editor`, `require_admin`) gating publication endpoints to Admins only.
5. **Catalogue-Driven Viewer**: Responsive, fast child viewer discovery experience reading static published catalogue endpoints.
