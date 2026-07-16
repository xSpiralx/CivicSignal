# ADR 0011: Versioned governed resources

Status: accepted

CivicSignal stores governance state in a stable `governed_resources` aggregate and keeps resource
content in immutable numbered `resource_revisions`. The working and published revision identifiers
are separate, so edits never change public data before verification and publication. Review and
verification decisions are append-oriented records tied to the exact revision considered.

Publication materializes the approved snapshot into the existing public organization, service,
source, and verification tables. This preserves the small, read-optimized public API while keeping
internal workflow fields out of public schemas. Optimistic concurrency uses the expected revision
number and returns HTTP 409 for stale actions. Records are archived rather than deleted.

This design deliberately avoids event sourcing. Audit events explain sensitive actions, immutable
revisions preserve content history, and decision records preserve trust evidence.
