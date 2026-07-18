# Deployment runbook

1. Complete `docs/release/v1.0-checklist.md` and merge a green commit.
2. Provision the Render Blueprint only with the account owner's approval; its current services use
   paid plans.
3. Configure `PUBLIC_BASE_URL`, `CORS_ORIGINS`, generated staging access credentials, database
   credentials, secure cookies, allowed hosts, and restricted administrator access.
4. Keep `NEXT_PUBLIC_DATA_MODE=demo` unless the DC human-review checklist has been completed.
5. Run migrations before starting the API. Seed fictional data explicitly for demo mode.
6. Verify HTTPS, `/api/health`, API `/health/ready`, public pages, authentication, CSRF, secure cookie
   flags, corrections, audit permissions, and log redaction.
7. Record the deployment URL and immutable image/commit identifier in the release notes.

The repository contains no Render credential, installed Render CLI, or approved paid-service
provisioning context. Deployment therefore requires an account-owner action and cannot be claimed
complete from local validation.
