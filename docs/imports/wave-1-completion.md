# Wave 1 completion report — HRSA 2026

## Executive summary

CivicSignal now has an additive, governed nationwide candidate pipeline and a private administrator review experience. One authoritative federal source was approved: HRSA Health Center Service Delivery and Look-Alike Sites, updated 2026-07-16 with a daily refresh cycle and usage limitations listed as none. The 2026 snapshot produced 18,953 private high-risk healthcare candidates across 38 idempotent batches. It created zero governed drafts and zero public services.

## Architecture and controls

- Source registry: 1 approved/enabled, 3 under review, 1 restricted, 3 grouped rejected entries in the documented registry.
- Freshness: only 2025–2026 record or dataset dates; retrieval is separate.
- Geography: city, county, state/territory, ZIP, local/state/multistate/nationwide and remote flags.
- Import: bounded JSON/CSV, per-file transactions, checkpoints, resume tokens, payload idempotency, quarantine summaries, cancellation state and three-worker backpressure during the one-time wave.
- Security: source allowlists, SSRF/DNS-rebinding protection, byte/type/depth/row limits, duplicate JSON-key and CSV-formula rejection, RBAC, CSRF, optimistic versions and audit events.
- Review: server-side search, filters, stable pagination, high-risk priority, source/license/freshness evidence, claim, defer, reject, source-review and single-record approval-as-draft.
- Publication boundary: candidate tables are absent from public APIs; approval creates only an immutable governed draft. Separate verification and publication remain required.

## Exact production results

| Measure | Result |
| --- | ---: |
| Official source records processed | 18,953 |
| Private candidates created | 18,953 |
| Import batches | 38 |
| Sources imported | 1 |
| Distinct state/territory codes represented | 60 |
| Distinct cities represented | 4,387 |
| Old records rejected | 0 |
| Missing-date records quarantined | 0 |
| Import failures | 0 |
| Exact/possible duplicates against the empty published directory | 0 |
| Published conflicts | 0 |
| High-risk candidates | 18,953 |
| Ready for Robert's review | 18,953 |
| Governed drafts created by import | 0 |
| Public services created by import | 0 |
| Production database size after import | 75,030,528 bytes (about 71.6 MiB) |

The geographic count includes U.S. states, D.C., territories, freely associated states represented by HRSA, and HRSA's `XX` nonstandard/unspecified code. It is not a completeness claim.

## Source decisions

HRSA/BPHC is approved for the bounded snapshot because the official catalog identifies the publisher, reports a 2026 update and daily refresh cycle, and lists usage limitations as none. HRSA attribution and the exact landing page are retained. Data.gov remains discovery-only. Municipal/state webpages and 211 remain restricted without explicit reuse rights. Findhelp and consumer map directories remain rejected.

## Validation and impact

Backend formatting, linting, strict typing, migrations and tests pass. Frontend formatting, TypeScript, linting and component tests pass. The production migration is additive. Public search remains stable and empty because Robert has not approved, verified or published any candidate.

Manual browser review should start with a small sample from each state, prioritizing high-risk records with missing contact fields and HRSA's `XX` geography. After approval as draft, verify current phone, official site, services and location before advancing through the existing publication workflow.

Administrator URL: <https://civicsignal-the-spiral-forge.vercel.app/admin/import-candidates>

Suggested commit title: `feat: add nationwide governed resource intake`

Suggested summary:

- add approved-source registry and current-data license reviews
- import 18,953 legally reusable 2026 HRSA records as private review candidates
- normalize candidates by city, county, state, ZIP and service area
- add idempotent bounded ingestion, freshness enforcement and duplicate detection
- create an administrator-only nationwide candidate review queue
- preserve explicit verification and publication as separate human decisions
- add high-risk safeguards, capacity controls, tests and operations documentation
