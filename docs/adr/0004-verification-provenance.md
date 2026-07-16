# ADR 0004: Verification and provenance
Status: Accepted
## Context
“Verified” must be evidence-based and historical review must survive updates.
## Decision
Require sources and append verification events. Centralize public visibility around the latest event and active state; restrict destructive foreign-key cascades.
## Alternatives considered
A boolean verified flag; free-form status text.
## Consequences
Public policy is auditable; future administration must preserve event history and define reviewer identity safely.
