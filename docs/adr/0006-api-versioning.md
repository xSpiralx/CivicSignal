# ADR 0006: Public API versioning
Status: Accepted
## Context
Public consumers need stable contracts independent from ORM structure.
## Decision
Expose explicit read schemas under `/api/v1`; never serialize ORM models directly.
## Alternatives considered
Unversioned REST; GraphQL first.
## Consequences
Breaking changes require a new version or migration period; schemas prevent internal-note leakage.
