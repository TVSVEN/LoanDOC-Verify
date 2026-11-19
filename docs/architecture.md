# Architecture

The MVP is a dependency-light Python HTTP application with a static HTML/CSS/JavaScript interface and SQLite persistence. It provides the same functional boundaries as the blueprint’s React/Spring Boot/FastAPI stack while keeping the hackathon demo easy to start.

```text
Applicant / loan officer browser
          | JSON + multipart
          v
Python HTTP API (app.py)
  ├── SQLite application, document, check, request, review and event records
  ├── local upload storage + SHA-256 duplicate detection
  ├── extraction/classification/quality tool functions
  └── verification orchestrator -> evidence checks -> next-action routing
```

The orchestrator calls deterministic tools for document requirements, PAN structure, identity comparisons, income comparisons, statement coverage, duplicate hashes and report generation. Each finding stores source document names, fields, values and a short explanation. Low certainty and discrepancies route to clarification or human review. No tool can approve a loan or declare fraud.

## API

- `GET /api/dashboard`, `GET /api/applications`, `POST /api/applications`
- `GET /api/applications/{id}`, `PUT /api/applications/{id}`, `DELETE /api/applications/{id}`
- `GET /api/applications/{id}/documents`, `POST /api/applications/{id}/documents`, `DELETE /api/documents/{id}`
- `POST /api/applications/{id}/verification/start`, `GET /api/applications/{id}/verification/results`
- `GET /api/applications/{id}/verification/report`, `GET /api/applications/{id}/requests`
- `GET /api/admin/review-cases`, `POST /api/admin/review-cases/{id}/resolve`

API routes require a signed-in account except for health checks and static assets. Applicant and officer roles are stored on the account. Application queries are scoped to the owner for applicants and to explicitly accepted `application_access` records for officers. Invitation tokens are stored as SHA-256 hashes, expire after 24 hours, and are accepted once. Use Docker Compose for an isolated local instance with a persistent named volume.
