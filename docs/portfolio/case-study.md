# CivicSignal case study

## Project overview

CivicSignal is a full-stack portfolio project demonstrating how a community-resource directory can
publish useful information without treating mutable records as ordinary CRUD data. It combines a
public, source-aware directory with permissioned correction, re-verification, immutable revision,
and audit workflows. Every included organization and service is fictional.

## Problem

Community directories become unreliable when hours, eligibility, access details, and contact
channels change. Immediate edits are fast but erase provenance; unattended reports are safe but do
not improve the directory. CivicSignal models the middle: public reports enter a governed workflow,
humans verify evidence, and publication preserves both the prior state and the decision history.

## Engineering challenge

The central challenge was keeping public reads simple while making writes deliberate. A resource
has separate working and published revision pointers. Proposed edits create immutable numbered
revisions, optimistic version checks reject stale writes, server-side readiness checks gate
publication, and the final verification updates related records transactionally. Automated stale
detection creates work without duplicating active tasks.

## Architecture

The responsive Next.js application serves public and administrator experiences and proxies browser
requests to a FastAPI API. FastAPI applies Pydantic validation, HTTP-only opaque sessions, CSRF
checks, role permissions, and workflow rules. SQLAlchemy and Alembic manage PostgreSQL. Docker
Compose supplies repeatable local services; Render configuration describes a noindex staging
environment and scheduled stale-detection job.

## Difficult problems solved

- Immutable resource revisions with independent working and published pointers.
- Conflict-safe updates using expected task and revision versions.
- Atomic verified publication that preserves the earlier revision.
- Public correction triage linked to operational re-verification tasks.
- Idempotent stale detection with PostgreSQL advisory locking and duplicate-task prevention.
- Opaque session authentication, CSRF protection, role-based authorization, and session revocation.
- Accessible application dialogs with focus containment, restoration, and keyboard operation.
- Structured audit events that avoid exposing reporter contact details publicly.

## Tradeoffs

Human verification is slower than direct editing, but it protects provenance and makes uncertainty
visible. Rich governance introduces more tables and states than CRUD, but it enables review,
rollback reasoning, and auditability. Public correction intake improves access but requires bounded
validation, duplicate mitigation, privacy guidance, and rate limiting. Docker improves parity while
adding local resource cost. The project intentionally defers automated fetching, maps, national
coverage, and AI recommendations.

## Testing

At the portfolio checkpoint the repository had 27 passing backend tests and 12 passing frontend
component tests, strict Python and TypeScript checks, lint/format gates, an optimized Next.js build,
and healthy Docker-backed PostgreSQL/API/web services. Browser, accessibility, persistence, and
security outcomes are recorded in the checkpoint report rather than implied by unit tests.

## Security, privacy, and accessibility

Concrete controls include Argon2 password hashing, HTTP-only sessions, absolute and idle expiry,
CSRF tokens, permission checks, trusted-host configuration, secure-cookie staging defaults, no-store
administrator responses, output schemas, bounded correction intake, and structured logs. Public
search does not require an account and application code does not retain search terms. Semantic
landmarks, skip links, labelled native controls, visible focus, reduced-motion/transparency styles,
and tested dialog focus behavior form the accessibility baseline; this is not a certification claim.

## Lessons learned

Data integrity is primarily a workflow design problem. Immutability is most useful when paired with
clear pointers and transaction boundaries. Concurrency errors must preserve a user’s work and offer
a recovery path. Demo data is part of product quality: it must be varied, safe, and explicit about
being fictional. Finally, honest release evidence is more persuasive than broad readiness claims.

## Future improvements

The bounded next step is controlled CSV/JSON import with dry-run preview and row-level validation.
Optional later work includes controlled export, approved-source ingestion with an SSRF boundary,
geospatial discovery, a verified real-data pilot, and public beta operations.
