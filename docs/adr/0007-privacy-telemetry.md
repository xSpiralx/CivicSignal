# ADR 0007: Privacy-first telemetry
Status: Accepted
## Context
Searches may reveal sensitive needs.
## Decision
Do not persist or log query strings, precise coordinates, profiles, or advertising identifiers. Collect only bounded aggregate operations data by default.
## Alternatives considered
Full analytics; session replay.
## Consequences
Less product-behavior data is available; operators must preserve these defaults in proxies and vendors.
