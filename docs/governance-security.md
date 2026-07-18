# Governance security foundation

This document describes the identity and governed trust-workflow foundation. Resource corrections
and operational re-verification now have permissioned APIs and administrator interfaces. Imports,
exports, independent review, and complete browser validation remain release blockers.

## Administrator bootstrap

Apply migrations, then create the first administrator interactively:

```bash
cd apps/api
civicsignal admin create --email admin@example.org --display-name "Site administrator"
```

The command reads and confirms the password without echo, enforces a 14–256 character policy,
normalizes the email, refuses duplicates, assigns the administrator role, and writes an audit
event in the same transaction. It never runs during application startup.

## Authentication and sessions

Passwords use Argon2id with versioned parameters and are rehashed after a successful login when
parameters become outdated. Login failures use the same public response for known and unknown
accounts. Known accounts receive a progressive temporary cooldown after five failures; this is a
defense layer, not a replacement for an edge rate limiter.

Successful login creates independent 384-bit opaque session and CSRF secrets. Only SHA-256 hashes
are stored. The raw session secret is returned in an `HttpOnly`, `SameSite=Strict` cookie scoped to
`/api/v1/admin`; `Secure` is mandatory through `COOKIE_SECURE=true` in production. Sessions have
absolute and idle expiration, are rejected for disabled accounts, and become invalid after a
password change. Logout revokes rather than deletes the record.

The sign-in response supplies the CSRF token to the authenticated application in memory. Every
authenticated state-changing request must send it in `X-CSRF-Token`; the server compares its hash
in constant time. The token must never be persisted in browser storage. XSS remains capable of
acting as the current user, so the future administrator UI must maintain a strict CSP.

## Authorization and audit

The backend maps five roles to explicit permissions in `policy.py`. Permissions are deny-by-default
and derived only from database roles. Authentication and bootstrap actions create append-oriented
audit rows without credentials, cookies, CSRF values, or request bodies.

## Residual risks and unavailable behavior

- Network-aware distributed rate limiting still belongs at the trusted reverse proxy.
- Account/session management endpoints and password reset are not implemented.
- Database-level audit immutability and the audit viewer are not implemented.
- Some governance actions still use legacy browser prompts and require accessible-dialog remediation.
- No deployment is approved by this milestone.
