# ACT Rave Mock API

Mock clinical-source API used by the **ACT (Automated Case Transfer)** hands-on data platform.

This repository simulates a Rave-like clinical source system backed by PostgreSQL and exposed through FastAPI. The API intentionally returns mixed payload formats (JSON, XML, and CSV) so the downstream ingestion platform can practice realistic parsing, validation, incremental extraction, retries, rate limiting, and multi-study processing.

---

## 1. What this repository does

```text
PostgreSQL
    ↓
FastAPI
    ↓
8 Clinical APIs
    ↓
JSON / XML / CSV
    ↓
ACT Data Platform (Airflow)
```

The source API is **read-only for the ACT pipeline**. ACT extracts data using `GET` endpoints. Database inserts/updates are performed only to create test scenarios.

---

## 2. Clinical entities

| Entity | Endpoint | Response format |
|---|---|---|
| Study | `/studies` | JSON |
| Site | `/sites` | CSV |
| Subject | `/subjects` | JSON |
| Visit | `/visits` | XML |
| Adverse Event | `/adverse-events` | XML |
| Lab Result | `/lab-results` | JSON |
| Protocol Deviation | `/protocol-deviations` | CSV |
| Data Query | `/data-queries` | XML |

All collection endpoints support study-level processing through `study_id` and incremental extraction through `updated_since`.

Typical query parameters:

```text
study_id=<study>
updated_since=<ISO-8601 timestamp>
offset=<integer>
limit=<1-100>
```

---

## 3. Repository structure

```text
act-rave-fastapi/
├── .devcontainer/
│   ├── devcontainer.json
│   └── docker-compose.yml
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── rate_limit.py
│   └── routers/
│       ├── __init__.py
│       ├── common.py
│       ├── studies.py
│       ├── sites.py
│       ├── subjects.py
│       ├── visits.py
│       ├── adverse_events.py
│       ├── lab_results.py
│       ├── protocol_deviations.py
│       └── data_queries.py
├── scripts/
│   └── init_database.py
├── sql/
│   └── init_db.sql
├── tests/
├── requirements.txt
└── README.md
```

---

## 4. Local lab database

The Codespaces/devcontainer PostgreSQL service is named:

```text
postgres
```

Lab connection values:

```text
Host:     postgres
Port:     5432
Database: rave_db
User:     rave_user
Password: rave_password
```

These credentials are for the local hands-on lab only. Do not reuse them in a real environment.

---

# START / STOP RUNBOOK

## 5. Start the Rave API

Open a terminal in the Rave API repository:

```bash
cd /workspaces/act-rave-fastapi
```

If the repository uses a Python virtual environment, activate it first:

```bash
source .venv/bin/activate
```

Check that PostgreSQL is running:

```bash
docker compose -f .devcontainer/docker-compose.yml ps
```

Start PostgreSQL if required:

```bash
docker compose -f .devcontainer/docker-compose.yml up -d postgres
```

Start FastAPI in development mode:

```bash
fastapi dev app/main.py --host 0.0.0.0 --port 8000
```

Keep this terminal running while Airflow extracts data.

Expected local API address:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

ReDoc documentation:

```text
http://127.0.0.1:8000/redoc
```

In GitHub Codespaces, open forwarded **port 8000** from the **PORTS** tab when browser access is required.

---

## 6. Stop the Rave API

Normal stop:

```text
CTRL + C
```

This stops FastAPI only. PostgreSQL can remain running.

To stop only PostgreSQL:

```bash
docker compose -f .devcontainer/docker-compose.yml stop postgres
```

To start PostgreSQL again:

```bash
docker compose -f .devcontainer/docker-compose.yml start postgres
```

---

# HEALTH CHECKS

## 7. Check that FastAPI is alive

```bash
curl -i http://127.0.0.1:8000/health
```

Also test the root endpoint:

```bash
curl -i http://127.0.0.1:8000/
```

Check all studies:

```bash
curl "http://127.0.0.1:8000/studies"
```

For the current multi-study lab, the response should contain both:

```text
ONC101
ONC102
```

---

## 8. Test study filtering

Study:

```bash
curl "http://127.0.0.1:8000/studies?study_id=ONC102"
```

Sites:

```bash
curl "http://127.0.0.1:8000/sites?study_id=ONC102"
```

Subjects:

```bash
curl "http://127.0.0.1:8000/subjects?study_id=ONC102"
```

Visits:

```bash
curl "http://127.0.0.1:8000/visits?study_id=ONC102"
```

Adverse events:

```bash
curl "http://127.0.0.1:8000/adverse-events?study_id=ONC102"
```

Lab results:

```bash
curl "http://127.0.0.1:8000/lab-results?study_id=ONC102"
```

Protocol deviations:

```bash
curl "http://127.0.0.1:8000/protocol-deviations?study_id=ONC102"
```

Data queries:

```bash
curl "http://127.0.0.1:8000/data-queries?study_id=ONC102"
```

---

## 9. Test pagination

Example:

```bash
curl "http://127.0.0.1:8000/adverse-events?study_id=ONC101&offset=0&limit=2"
```

The API supports a maximum page size of 100 records.

---

## 10. Test incremental extraction manually

Example:

```bash
curl --get \
  --data-urlencode "study_id=ONC101" \
  --data-urlencode "updated_since=2026-08-16T08:00:00+00:00" \
  "http://127.0.0.1:8000/adverse-events"
```

The source API uses a strict timestamp boundary:

```text
updated_at > updated_since
```

The downstream data platform therefore applies a small overlap window to reduce the risk of missing records at the timestamp boundary.

---

# DATABASE COMMANDS

## 11. Check PostgreSQL status

```bash
docker compose -f .devcontainer/docker-compose.yml ps postgres
```

PostgreSQL readiness check:

```bash
docker compose -f .devcontainer/docker-compose.yml exec postgres \
  pg_isready -U rave_user -d rave_db
```

---

## 12. Open PostgreSQL CLI

```bash
docker compose -f .devcontainer/docker-compose.yml exec postgres \
  psql -U rave_user -d rave_db
```

Exit `psql`:

```text
\q
```

---

## 13. Quick database row-count check

```bash
docker compose -f .devcontainer/docker-compose.yml exec postgres \
  psql -U rave_user -d rave_db -c "
SELECT 'study' entity, COUNT(*) records FROM study
UNION ALL SELECT 'site', COUNT(*) FROM site
UNION ALL SELECT 'subject', COUNT(*) FROM subject
UNION ALL SELECT 'visit', COUNT(*) FROM visit
UNION ALL SELECT 'adverse_event', COUNT(*) FROM adverse_event
UNION ALL SELECT 'lab_result', COUNT(*) FROM lab_result
UNION ALL SELECT 'protocol_deviation', COUNT(*) FROM protocol_deviation
UNION ALL SELECT 'data_query', COUNT(*) FROM data_query;
"
```

---

## 14. Verify studies in PostgreSQL

```bash
docker compose -f .devcontainer/docker-compose.yml exec postgres \
  psql -U rave_user -d rave_db \
  -c "SELECT study_id, study_name, updated_at FROM study ORDER BY study_id;"
```

---

## 15. Create an incremental-change test

Example: modify only one ONC102 adverse event.

```sql
UPDATE adverse_event
SET
    severity = 'SEVERE',
    updated_at = CURRENT_TIMESTAMP
WHERE ae_id = 'AE10201';
```

Verify it:

```sql
SELECT
    ae_id,
    subject_id,
    event_term,
    severity,
    updated_at
FROM adverse_event
WHERE ae_id = 'AE10201';
```

Important: this lab intentionally updates `updated_at` explicitly rather than using database triggers.

---

# DEBUGGING

## 16. API does not open

Check whether port 8000 is listening:

```bash
curl -i http://127.0.0.1:8000/health
```

Check the process using the port:

```bash
lsof -i :8000
```

If no FastAPI process is running, start it again:

```bash
fastapi dev app/main.py --host 0.0.0.0 --port 8000
```

---

## 17. PostgreSQL connection failure

Check the container:

```bash
docker compose -f .devcontainer/docker-compose.yml ps postgres
```

Check PostgreSQL logs:

```bash
docker compose -f .devcontainer/docker-compose.yml logs --tail=100 postgres
```

Check readiness:

```bash
docker compose -f .devcontainer/docker-compose.yml exec postgres \
  pg_isready -U rave_user -d rave_db
```

---

## 18. API returns HTTP 429

The mock API intentionally implements rate limiting to simulate a real source-system constraint.

Current lab limits:

```text
10 requests / second
20 requests / 5 seconds burst window
```

If a manual test returns `429 Too Many Requests`, wait briefly instead of repeatedly refreshing the endpoint. The downstream Rave API client handles retry/backoff behavior.

---

## 19. API returns the wrong study

Verify the source rows first:

```sql
SELECT study_id, COUNT(*)
FROM subject
GROUP BY study_id
ORDER BY study_id;
```

For child entities such as visits, adverse events, labs, deviations, and data queries, study ownership is derived through joins rather than duplicating `study_id` physically in every child table.

Example check:

```sql
SELECT
    s.study_id,
    ae.ae_id,
    ae.subject_id,
    ae.updated_at
FROM adverse_event ae
JOIN subject s
  ON s.subject_id = ae.subject_id
ORDER BY s.study_id, ae.ae_id;
```

---

## 20. API payload/content-type problem

Use headers during debugging:

```bash
curl -i "http://127.0.0.1:8000/adverse-events?study_id=ONC101"
```

Expected formats:

```text
Study                 application/json
Site                  text/csv
Subject               application/json
Visit                 application/xml
Adverse Event         application/xml
Lab Result            application/json
Protocol Deviation    text/csv
Data Query            application/xml
```

If the endpoint payload and content type do not match the downstream endpoint configuration, the data platform should fail rather than silently parse the wrong format.

---

## 21. Codespaces browser URL does not open

Use the **PORTS** tab and verify that port `8000` is forwarded.

A Codespaces forwarded URL normally follows this form:

```text
https://<codespace-name>-8000.app.github.dev
```

For terminal-to-terminal calls inside the same Codespace, prefer:

```text
http://127.0.0.1:8000
```

---

# MULTI-STUDY TEST

## 22. Verify ONC101 and ONC102 end to end

Database:

```bash
docker compose -f .devcontainer/docker-compose.yml exec postgres \
  psql -U rave_user -d rave_db \
  -c "SELECT study_id, study_name FROM study ORDER BY study_id;"
```

API:

```bash
curl "http://127.0.0.1:8000/studies"
```

Study-specific adverse events:

```bash
curl "http://127.0.0.1:8000/adverse-events?study_id=ONC101"
```

```bash
curl "http://127.0.0.1:8000/adverse-events?study_id=ONC102"
```

The downstream Airflow DAG should discover both studies dynamically. Do not hard-code the list of studies in the data platform.

---

# SAFE RESET / RESTART GUIDANCE

## 23. Normal restart sequence

```text
1. CTRL+C FastAPI
2. Confirm PostgreSQL is healthy
3. Start FastAPI again
4. Run /health
5. Run /studies
6. Start/trigger the downstream Airflow pipeline
```

Avoid deleting the PostgreSQL volume merely to fix an application problem. Removing the volume destroys lab data and should only be done when an intentional full database reset is required.

---

# GIT CHECKS

## 24. Before committing

```bash
git status
git diff
```

Make sure secrets or local environment files are not staged.

Typical commit flow:

```bash
git add .
git status
git commit -m "Describe the change"
git push
```

Never commit real credentials, access tokens, or `.env` files.

---

# QUICK COMMAND CHEAT SHEET

```bash
# Go to repo
cd /workspaces/act-rave-fastapi

# PostgreSQL status
docker compose -f .devcontainer/docker-compose.yml ps postgres

# Start PostgreSQL
docker compose -f .devcontainer/docker-compose.yml up -d postgres

# PostgreSQL logs
docker compose -f .devcontainer/docker-compose.yml logs --tail=100 postgres

# Start FastAPI
fastapi dev app/main.py --host 0.0.0.0 --port 8000

# Health
curl -i http://127.0.0.1:8000/health

# Studies
curl "http://127.0.0.1:8000/studies"

# ONC102 adverse events
curl "http://127.0.0.1:8000/adverse-events?study_id=ONC102"

# Stop FastAPI
# CTRL+C
```

---

# Production note

This repository is a **source-system simulator for development and interview/hands-on practice**. Production clinical integrations would require enterprise authentication, source-system contracts, approved API credentials, encryption, audit controls, secrets management, monitoring, and validated operational procedures.

---

## Official references

- FastAPI CLI: https://fastapi.tiangolo.com/fastapi-cli/
- FastAPI bigger applications / entrypoints: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- GitHub Codespaces port forwarding: https://docs.github.com/en/codespaces/developing-in-a-codespace/forwarding-ports-in-your-codespace


#to get current token to update in act_data_platform
echo $GITHUB_TOKEN