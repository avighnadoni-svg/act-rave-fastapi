# ACT Rave Mock API

Read-only FastAPI project for the ACT project. It simulates separate Rave-style JSON endpoints and is ready for GitHub Codespaces.

## Implemented

- GET-only source APIs
- 8 separate endpoints
- GET by ID
- Query filters
- Pagination with `offset` / `limit` (max 100)
- `X-Total-Count` response header
- Incremental extraction using `updated_since`
- Mock `updated_at` source metadata
- Rate limiting: 10 requests/second and 20 requests/5 seconds per client
- HTTP 429 with `Retry-After`
- 404 and standard server errors
- Swagger `/docs`
- Health endpoint `/health`
- GitHub Codespaces devcontainer
- GitHub Actions tests
- Example async extraction client with 30s timeout, retry/exponential backoff, pagination, and bounded parallel GET calls

## Endpoints

```text
GET /studies
GET /sites
GET /subjects
GET /visits
GET /adverse-events
GET /lab-results
GET /protocol-deviations
GET /data-queries
```

Examples:

```text
GET /adverse-events?serious=Y
GET /subjects?site_id=SITE01
GET /sites?offset=0&limit=2
GET /adverse-events?updated_since=2026-02-08T12:00:00Z
```

## Run in GitHub Codespaces

```bash
pip install -r requirements.txt
fastapi dev app/main.py --host 0.0.0.0 --port 8000
```

Open `/docs` for Swagger UI.

## Run the ACT extraction client

With the API running:

```bash
python client/extract.py
```

The client demonstrates how the consumer side handles pagination, 30-second timeout, retries, `429 Retry-After`, and parallel GET extraction while limiting concurrency.

## Test

```bash
pytest -q
```

## Important

This is a mock ACT/Rave-style API built from the sample project payloads. It does not claim to reproduce the real Medidata Rave API contract.
