# Peblo TV Mini — Backend

A FastAPI backend for the Peblo TV Mini kids content management system.

## Quick Start

```bash
# Start PostgreSQL (main + test)
docker compose up -d db db_test

# Install dependencies
cd backend
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Import seed data
python -m app.scripts.seed

# Start development server
uvicorn app.main:app --reload --port 8000
```

## Running Tests

Tests require the `peblo_test` PostgreSQL container running on port 5433:

```bash
docker compose up -d db_test
cd backend
pytest -v
```

Artwork-only unit tests (no DB needed):

```bash
pytest tests/test_artwork.py -v
```

## Architecture

### Authentication
- JWT (`HS256`) issued at `POST /api/v1/auth/token`
- Roles: `editor` (CRUD content, upload artwork, see validation report) and `admin` (everything + publish catalogue)
- Enforced in FastAPI dependencies (`require_editor`, `require_admin`) — no frontend trust

### Publishing Pipeline

```
POST /admin/catalog/publish  (admin only)
          │
          ▼
   1. run_validation()
      └─ if blocking issues → 422 (old catalogue untouched)
          │
          ▼
   2. create PublishRun sentinel (status="running")
          │
          ▼
   3. build_catalog() — in memory
          │
          ▼
   4. storage.put("catalog_<run_id>.json")
          │
          ▼
   5. storage.atomic_replace(tmp → catalog.json)
      └─ local: os.replace()  (atomic on POSIX; best-effort on Windows NTFS)
      └─ S3/MinIO: copy + delete
          │
          ▼
   6. update PublishRun → status="success"
```

**Atomicity guarantee**: A reader can never observe a partially-written `catalog.json`. If the process dies between steps 4 and 6, the temporary file is orphaned and the previous `catalog.json` remains valid.

### Validation Report

`GET /admin/validation/report` (editor+)

Returns all issues grouped by entity type with severity:

| Code | Severity | Condition |
|------|----------|-----------|
| `MISSING_SECTION` | **blocking** (published), **warning** (draft) | Show has no section assigned |
| `INVALID_SECTION` | **blocking** | Section value not in `reference.json` |
| `MISSING_ARTWORK` | **blocking** | Published episode has no artwork |
| `MISSING_DURATION` | **blocking** | Published episode has no duration |
| `DUPLICATE_CONTENT_GROUP_LANG` | **blocking** | Two episodes share same `(content_group, language)` |
| `CONTENT_GROUP_IDENTITY_CONFLICT` | **blocking** | Language variants in same content_group disagree on episode_number/show/season |
| `NO_PUBLISHED_EPISODES` | warning | Published show has no published episodes |
| `TITLE_ALL_CAPS` | warning | Episode title is ALL-CAPS |
| `TITLE_ALL_LOWERCASE` | warning | Episode title is all-lowercase |

### Language Grouping

Two episodes sharing the same `content_group` but different `language` values collapse into **one** catalogue entry:

```json
{
  "content_group": "moti-s01e01",
  "title": "A New Home",
  "languages": ["en", "hi"],
  "duration_seconds": 240
}
```

If two episodes share the same `(content_group, language)` — which is invalid — the validator surfaces this as a **blocking** issue and blocks publishing until resolved.

If cross-language variants disagree on `episode_number`, `show_id`, or `season_id`, a `CONTENT_GROUP_IDENTITY_CONFLICT` blocking issue is raised.

### Season 0 (Trailers)

Season 0 episodes are separated into `show.trailers[]` in the catalogue. They do **not** appear in `show.seasons[]` and are **not** renumbered or merged with regular episodes.

### Deterministic Ordering

The catalogue always uses explicit, stable sort keys — never relying on PostgreSQL row order or Python dict/set hash randomness:

- **Sections**: reference.json order (featured → series → minisodes → songs)
- **Shows within a section**: `(title.lower(), id)` — alphabetical, UUID tie-breaker
- **Seasons**: `season_number` ascending
- **Episodes within a season**: `(episode_number, content_group)` — episode number first, content_group as tie-breaker

Repeated publishing of unchanged source data always produces an equivalent catalogue JSON.

### Catalogue Search

`GET /catalog/search?q=&category=&language=&section=`

Filters compose with **AND** semantics:
- **q**: substring match on show title, episode title, or any category
- **category**: show must have this category
- **language**: episode must support this language
- **section**: show must be in this section

**Why in-memory search is acceptable for this dataset:**

The published catalogue is ~95 source rows (after content_group collapsing, fewer unique episodes). At this scale:
- The catalogue JSON is < 50 KB
- Each search query reads one file and scans it in < 1ms
- No database query is needed — zero connection overhead
- The filter logic is simple Python list comprehensions

**When this stops scaling:**
- Above ~5,000 unique episodes the JSON will exceed 5 MB and per-request memory becomes a concern
- Above ~50,000 episodes, O(n) scan latency becomes noticeable (> 100ms)
- Concurrent requests each holding the full catalogue in memory wastes RAM
- For that scale: move to PostgreSQL full-text search (`tsvector`) or Elasticsearch/Typesense, and cache popular queries with Redis

### Artwork Validation

Upload uses Pillow to detect the **actual** image format from bytes — never trusting the HTTP `Content-Type` header or filename extension alone.

| Kind | Aspect ratio | Max size |
|------|-------------|----------|
| poster | 2:3 (portrait) | 200 KB |
| banner | 16:9 (landscape) | 200 KB |
| thumbnail | 16:9 (landscape) | 200 KB |

Accepted formats: JPEG, PNG, WebP.

### Storage Backends

| Backend | Config | Use case |
|---------|--------|---------|
| `local` | `LOCAL_STORAGE_PATH` | Development / tests |
| `minio` | `MINIO_*` env vars | Self-hosted S3-compatible |

Switch with `STORAGE_BACKEND=local|minio`.

## Environment Variables

See `.env.example` for all required variables.

## Seed Data

The seed importer (`/admin/seed`) reads `seed_shows.json` and preserves intentional errors:

- **Rhyme Rangers** — `section=null` (blocking issue for published shows)
- **ep_0036** — published with `artwork_available=[]` (MISSING_ARTWORK)
- **ep_9001 / ep_0004** — duplicate `(motis-many-lives-s01e02, hi)` (DUPLICATE_CONTENT_GROUP_LANG)
- **motis-many-lives-s01e02** — title mismatch between Hindi variants (CONTENT_GROUP_IDENTITY_CONFLICT)

These intentional errors are preserved in the database and surfaced by the validation report rather than silently discarded.
