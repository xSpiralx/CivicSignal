# Five-to-eight-minute demonstration

## 1. Frame the problem (45 seconds)

“Community-resource information changes, but silently editing a public listing loses provenance.
CivicSignal is my full-stack demonstration of a safer correction-to-publication loop. Everything
shown is fictional.” Point out the demo banner and emergency disclaimer.

## 2. Public experience (60 seconds)

Open the directory, filter the varied fictional records, and select one. Show the provider, service
area, contact method, last-checked date, freshness state, and source. Mention that search requires no
account and verification is context—not a promise of availability.

## 3. Submit a correction (45 seconds)

Report changed hours. Explain bounded fields, optional contact information, duplicate mitigation,
rate limiting, and the guarantee that a report does not directly change public data.

## 4. Govern the change (2–3 minutes)

Sign in locally as an authorized operator. Claim the correction, record a reason, and escalate it.
Claim the re-verification task. Change the fictional hours in the proposed-revision editor, update
source provenance, save, and show server readiness plus the human-readable comparison. Explain the
separate working/published pointers and stale-write `409` recovery.

## 5. Verify and publish (60 seconds)

Open the accessible publication dialog, add evidence, and publish. Return to the public detail page
to show the updated hours and verification date. Explain that the transaction also completes the
task, resolves related corrections, recalculates freshness, and writes audit events while retaining
the prior revision.

## 6. Engineering close (60 seconds)

Briefly show the architecture diagrams and validation commands. Highlight FastAPI, Next.js,
PostgreSQL, Alembic, Docker, opaque sessions, CSRF, RBAC, advisory locking, automated stale
detection, semantic UI, strict typing, and tests. Close with honest limitations: fictional data,
portfolio-stage rather than production-ready, and no automated ingestion, maps, or national pilot.
