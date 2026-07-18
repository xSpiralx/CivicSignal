# ADR 0003: PostgreSQL

Status: Accepted

## Context

Resource integrity, filtering, transactions, and provenance require a relational store.

## Decision

Use PostgreSQL in deployment and SQLite only for bounded fast tests.

## Alternatives considered

Document databases; embedded databases in production.

## Consequences

Strong constraints and portable hosting; operators must maintain migrations and backups.
