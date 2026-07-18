# Optional paid private staging on Render

> This document describes an optional paid staging topology and is **not** the current
> `render.yaml`. The checked-in Blueprint now defines only the free release-candidate API described
> in `docs/operations/free-hosting-decision.md`. Do not create the topology below without explicit
> payment authorization.

The selected staging topology uses a public Next.js web service, a private FastAPI service, and a
paid managed PostgreSQL database in one Render region. Browser traffic reaches only Next.js; its
same-origin handlers call FastAPI over Render's private network. PostgreSQL has an empty public IP
allowlist. Render terminates TLS.

This is staging, not production. It uses fictional or specifically approved test records, is
protected with HTTP Basic authentication, emits `noindex`, disallows crawlers, and shows a visible
staging banner.

## Provisioning

1. Connect the CivicSignal GitHub repository to Render.
2. Create a separate private Blueprint or configure the services manually. Do not reuse the current
   free `render.yaml`. Review every resource and displayed monthly estimate before approval.
3. Provide `CORS_ORIGINS` and `PUBLIC_BASE_URL` using the assigned HTTPS web URL.
4. Set `STAGING_ACCESS_USERNAME` to a non-identifying tester username. Render generates the access
   password; copy it once into the team's approved password manager.
5. Wait for CI and the Blueprint pre-deploy `alembic upgrade head` command to succeed.
6. Open an API shell and run the interactive administrator command:

   ```bash
   civicsignal admin create --email ADMIN_EMAIL --display-name "Staging administrator"
   ```

   Share credentials only through the approved password manager. Create contributor, reviewer,
   and verifier accounts through the administrator UI with separate strong passwords.

## Required environment inventory

Backend configuration includes `ENVIRONMENT`, `DATABASE_URL`, `ALLOWED_HOSTS`, `CORS_ORIGINS`,
`COOKIE_SECURE`, `COOKIE_SAMESITE`, optional `COOKIE_DOMAIN`, session absolute and idle lifetimes,
`DEMO_MODE`, and `LOG_LEVEL`. Render supplies `PORT`; the API command binds to it. Render's
PostgreSQL URL is normalized to the asyncpg SQLAlchemy driver by application configuration.

Frontend configuration includes `NEXT_PUBLIC_APP_ENV`, `API_INTERNAL_URL`, `PUBLIC_BASE_URL`,
`STAGING_ACCESS_USERNAME`, `STAGING_ACCESS_PASSWORD`, and the fictional-data emergency notice.
Only variables prefixed with `NEXT_PUBLIC_` may enter the browser bundle; neither access password
nor database URL uses that prefix.

## Deployment and smoke test

Deployments occur only after GitHub checks pass. Migrations run before the API starts, and a failed
migration or health check leaves the previous successful deployment serving traffic.

After each deployment, authenticate through the staging access gate and verify:

- `/`, `/resources`, `/privacy`, and `/security` return successfully;
- `/api/health` returns 200;
- `/admin/sign-in` accepts the staging administrator;
- sign-out and session revocation work;
- a fictional draft can be created, revised, submitted, reviewed, verified, and published;
- the published record appears in `/resources` with its source and verification date;
- stale revision actions return 409;
- `/robots.txt` disallows all crawling and responses contain no indexing metadata.

## Monitoring and logs

Render health-checks the web service at `/api/health` and the private API at `/health/ready`.
Configure deploy-failure and service-health email notifications in the Render workspace. Application
logs are structured and exclude passwords, session tokens, CSRF values, and request bodies. Do not
enable request-body capture in platform log drains. External error tracking remains optional and
must receive a privacy review before adding a client SDK.

## Backup and restore

Paid Render PostgreSQL provides point-in-time recovery. Before a risky migration, create a logical
export from the database Recovery page and record its timestamp. For a restore drill, restore PITR
or the export into a new isolated database, run `alembic current`, verify a representative public
resource and audit record, then delete the drill database. Never test restoration over the active
staging database.

## Rollback

For an application regression, select the previous successful deployment in each service's Events
page and use **Rollback to this deploy**. Disable automatic deployment until the regression is
fixed. Application rollback does not reverse database writes or schema changes; use forward-fix
migrations when possible and switch to an independently verified recovery database only for data
loss. Re-run all smoke tests after rollback.

## Resetting staging

There is intentionally no automatic destructive reset command. To reset, create a fresh staging
database through the Blueprint, apply migrations, explicitly seed fictional data, verify it, and
only then delete the old database. This prevents a routine command from erasing tester-created
records.
