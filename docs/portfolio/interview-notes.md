# Interview notes

## Why did you build CivicSignal?

Public directories often optimize for finding records but not for keeping them trustworthy. I wanted
to demonstrate the engineering between “someone reported a change” and “the public can rely on a
traceable update.”

## What was the hardest technical problem?

Publication spans revisions, public materialized records, verification history, freshness, reports,
tasks, and audit events. The hard part was defining ownership and one transaction boundary so a
failure could not leave a partially published state.

## Why immutable revisions?

They preserve exactly what reviewers saw, support meaningful comparisons, and prevent historical
records from changing under completed verification decisions. Separate pointers distinguish work in
progress from public truth.

## How does optimistic concurrency work?

Mutations include the expected task version and revision number. The API locks the current task,
compares those values, and returns `409 Conflict` when another operator has moved the workflow. The
editor preserves local text and offers an explicit reload instead of overwriting newer work.

## How does a correction become a public change?

A report is triaged and escalated to a re-verification task. A verifier saves a sourced proposed
revision, reviews server readiness and comparison, supplies evidence, and publishes. Only that final
transaction moves the published pointer and updates the public service.

## How are duplicate tasks prevented?

The database enforces one active re-verification task per service and the stale-detection path uses a
PostgreSQL advisory lock. Repeated scans reuse existing work rather than multiplying it.

## How does stale detection work?

A deterministic service classifies each public resource from its verification dates. A CLI can run
the scan with a supplied timestamp or in dry-run mode; the scheduled job transitions due records,
creates missing tasks idempotently, and records an audit summary.

## How are authentication and CSRF handled?

Passwords use Argon2. Successful sign-in creates a hashed opaque session token in an HTTP-only
cookie with idle and absolute expiry. Mutating administrator requests also require a CSRF token, and
the API independently checks account state, role permissions, and session revocation.

## What changes at large production scale?

I would add a distributed rate limiter, managed observability and alerting, tested encrypted
backups, queue workers for bounded imports, stronger tenant/region modeling, load tests, and an
approved source and real-data governance program before broad public use.

## What tradeoffs did you make?

I chose human verification over automatic edits, explicit state transitions over generic CRUD, and
fictional depth over unverified breadth. That costs workflow complexity but makes data integrity and
limitations visible.

## What did you learn?

Concurrency and auditability need to be designed into the domain, not appended later. Accessible
error recovery matters as much as the happy path. A release claim should always map to reproducible
evidence.

## What work did you personally own?

I owned the product framing, architecture, data model, backend and frontend implementation, security
controls, tests, Docker/CI setup, documentation, and release validation represented in this
repository.

## What role did AI-assisted development play?

AI tools assisted with implementation, review checklists, and documentation. Material use follows
the repository policy: generated changes were inspected, formatted, type-checked, tested, and
validated against the running application. AI did not supply or verify resource facts.

## What is the release decision?

Stop feature development. The repository and local release gates are prepared, but public release
requires account-owner authorization for Vercel, Render, Neon, and GitHub secrets, plus named human
verification of records in every covered area. No real record is published merely because an AI
found a page, and nationwide searchability is never described as comprehensive coverage.
