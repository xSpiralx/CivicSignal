# ADR 0001: Monorepo

Status: Accepted

## Context

The API, web UI, infrastructure, and policy evolve together.

## Decision

Keep deployable apps under `apps`, future shared packages under `packages`, and operational knowledge under `docs`.

## Alternatives considered

Separate repositories; a single mixed application.

## Consequences

Atomic changes and unified CI are easier; tooling boundaries must remain explicit.
