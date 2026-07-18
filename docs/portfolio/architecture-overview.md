# Architecture overview

## System context

```mermaid
flowchart LR
  Visitor["Public visitor"] --> Web["Next.js web"]
  Operator["Authorized operator"] --> Web
  Web --> API["FastAPI API"]
  API --> DB[(PostgreSQL)]
  Scheduler["Scheduled stale-detection job"] --> APIData["Shared domain and database services"]
  APIData --> DB
```

The web layer renders the public directory and administrator UI, and exposes same-origin proxy
routes. The API owns validation, authorization, workflow state, and publication decisions.
PostgreSQL stores public directory data, governance revisions, accounts, sessions, work queues,
corrections, verifications, and audit events. Alembic owns schema evolution.

## Authentication and authorization

```mermaid
sequenceDiagram
  participant B as Browser
  participant W as Next.js proxy
  participant A as FastAPI
  participant D as PostgreSQL
  B->>W: Sign-in credentials
  W->>A: Same-origin request
  A->>D: Verify Argon2 password and create opaque session
  A-->>B: HTTP-only session cookie + CSRF token
  B->>W: Mutating request + CSRF token
  W->>A: Cookie and token
  A->>D: Session expiry, account, role, permission checks
  A-->>B: Authorized response
```

Contributor, reviewer, verifier, and administrator roles map to explicit permissions. Sensitive
routes enforce permissions at the API boundary; UI visibility is convenience rather than authority.

## Resource lifecycle

```mermaid
stateDiagram-v2
  [*] --> Draft
  Draft --> InReview: submit
  InReview --> NeedsVerification: advance
  NeedsVerification --> Verified: evidence recorded
  Verified --> Published: publish
  Published --> NeedsReverification: stale or correction
  NeedsReverification --> Published: verified revision
  Draft --> Rejected
  Published --> Archived
```

Governed resources use numbered immutable `ResourceRevision` records. `current_revision_id` points
to the working revision; `published_revision_id` remains stable until verified publication.

## Correction lifecycle

```mermaid
flowchart LR
  Report["Public correction"] --> Triage
  Triage -->|dismiss/duplicate| Closed["Closed report"]
  Triage --> Escalate["Re-verification task"]
  Escalate --> Proposal["Immutable proposed revision"]
  Proposal --> Verify["Evidence + readiness"]
  Verify --> Publish["Atomic publication"]
  Publish --> Resolve["Related reports resolved"]
  Publish --> Audit["Audit events"]
```

Reporter contact is optional and permission-restricted. Duplicate intake is mitigated without
revealing whether another person submitted the same report.

## Publication transaction

```mermaid
sequenceDiagram
  participant V as Verifier
  participant A as API transaction
  participant R as Revision records
  participant P as Public directory
  V->>A: Publish(expected task + revision, evidence)
  A->>A: Lock and validate task, permissions, readiness
  A->>R: Preserve prior revision and select proposed revision
  A->>P: Update materialized public service data
  A->>A: Record verification, freshness, report resolution, audit
  A-->>V: Commit completed task
```

Any exception before commit prevents partial publication.

## Freshness and scheduled work

```mermaid
flowchart TD
  Schedule["Daily Render cron or CLI"] --> Scan["Deterministic stale scan"]
  Scan --> Lock["PostgreSQL advisory lock"]
  Lock --> Classify["current / due soon / due / overdue / critical"]
  Classify --> Transition["Mark resources needing re-verification"]
  Transition --> Task["Create one active task when absent"]
  Task --> Audit["Structured audit summary"]
```

The CLI supports a dry run and deterministic timestamp. Repeated execution does not create duplicate
active work.

## Deployment and testing

Docker Compose runs PostgreSQL, the API, and web application locally. Render describes PostgreSQL,
private API, public web, health checks, TLS at the platform edge, secure staging cookies, a scheduled
job, and noindex behavior. CI runs Python formatting/Ruff/MyPy/pytest, frontend formatting/ESLint/
TypeScript/Vitest/build, Compose builds, migration-backed E2E, dependency review, secret scanning,
and CodeQL.
