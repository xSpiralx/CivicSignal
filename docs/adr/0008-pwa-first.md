# ADR 0008: PWA-first downloadable experience
Status: Accepted
## Context
Installability and an honest offline state help constrained devices without native-app complexity.
## Decision
Start with a web manifest and shell-only service worker. Never cache resource APIs until timestamped, visibly stale snapshots are designed.
## Alternatives considered
Native wrappers; broad cache-first service worker.
## Consequences
Offline users receive a warning rather than potentially dangerous stale records.
