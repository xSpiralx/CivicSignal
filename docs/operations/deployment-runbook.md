# Deployment runbook

1. Complete `docs/release/v1.0-checklist.md` and merge a green commit.
2. Create a Neon Free project without enabling paid capacity. Copy its pooled PostgreSQL URL into the
   Render `DATABASE_URL` secret and run the documented logical-export backup immediately.
3. Create the Render Blueprint from `render.yaml`. Confirm that the only resource is a **Free** API
   web service. Set its exact `*.onrender.com` hostname in `ALLOWED_HOSTS`.
4. Import the repository in Vercel Hobby with project root `apps/web`. This personal,
   non-commercial restriction is acceptable only while CivicSignal remains a portfolio project.
5. Generate two different 48-byte secrets locally. Store `PROXY_SHARED_SECRET` in Vercel and Render;
   store `MAINTENANCE_TOKEN` in Render and the GitHub Actions secret. Never use a `NEXT_PUBLIC_`
   prefix for either secret.
6. Configure Vercel `API_INTERNAL_URL` with the Render HTTPS URL, `PUBLIC_BASE_URL` with the Vercel
   URL, `NEXT_PUBLIC_APP_ENV=staging`, and `NEXT_PUBLIC_DATA_MODE=demo` for the first deployment.
7. Set Render `PUBLIC_FRONTEND_URL` and `CORS_ORIGINS` to the Vercel URL. Set `API_PUBLIC_URL` to the
   Render URL. The API start command runs `alembic upgrade head` before Uvicorn.
8. Create the initial administrator using `civicsignal admin create` through a secure Render shell.
   Do not seed demo accounts and remove any one-time shell history containing identifiers.
9. Set GitHub `PRODUCTION_MAINTENANCE_URL` to the Render
   `/internal/maintenance/detect-stale` endpoint and `PRODUCTION_MAINTENANCE_TOKEN` to the matching
   secret. Manually run the workflow once and retain its structured result.
10. Keep the deployment no-indexed and in fictional demo mode until every source and record selected
    for initial nationwide publication has a named human decision. Only then set
    `NEXT_PUBLIC_DATA_MODE=nationwide-public` and redeploy. Searchability is not a claim of complete
    coverage for any state, territory, county, city, or town.
11. Verify HTTPS, `/api/health`, API `/health/ready`, direct API rejection, authentication, CSRF,
    secure cookie flags, corrections, audit permissions, stale detection, backup, restore, and logs.
12. Record the URLs and immutable commit in the release report.

No GitHub, Vercel, Render, or Neon account credential is present in this checkout. Those external
authorizations and named human source/record reviews are required before a public release can be
claimed.
See [`free-hosting-decision.md`](free-hosting-decision.md) for current limits and rejected options.
