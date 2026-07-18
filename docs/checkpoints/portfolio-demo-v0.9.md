# Portfolio demo v0.9 checkpoint

Status language: CivicSignal is a portfolio-stage release candidate demonstrating governed resource
publishing, correction handling, verification, auditability, and freshness management using
fictional demo data. It is not production-ready and is not a real emergency directory.

## Completed evidence

- Docker Desktop, Compose, PostgreSQL, API, and web services restored and healthy on ports 8001/3001.
- Alembic at `20260718_0006 (head)`, seed repeatable, and stale dry run examined six records.
- Python formatting/Ruff/strict MyPy and 28 backend tests passed.
- Prettier/ESLint/strict TypeScript, 12 component tests, and the production build passed.
- Eight Playwright checks passed across desktop and mobile, including six axe scans with no serious
  or critical violations on the landing page, directory, and sign-in page.
- A fictional correction survived `docker compose stop` followed by `docker compose start` without
  deleting volumes.
- Browser validation proved public correction intake, administrator sign-in, session persistence,
  resource discovery/detail, semantic contact links, responsive 390px layout, and the guided
  dashboard.
- Curated fictional data, portfolio documentation, and five real application screenshots were added.

## Defects fixed during Docker/browser validation

- Alembic’s lowercase role records did not match SQLAlchemy’s default uppercase enum names.
- The API session cookie path did not match the browser-visible Next.js administrator proxy path.
- Concurrent initial/search requests could leave the directory stuck on an older result.
- Development CSP generated React debugging errors; production CSP remains strict.
- Landing category and repository links were inaccurate.
- The dashboard described implemented governance features as unavailable.
- A seeded location duplicated the word “Center,” and phone contacts were not actionable links.

## Remaining required portfolio blockers

- Add isolated, resettable browser fixtures for the full correction → governed proposal → verified
  publication flow, conflict, forbidden-role, and session-expiration scenarios.
- Complete manual VoiceOver, 200% zoom, keyboard-only administrator workflow, reduced-effects, and
  the full breakpoint matrix; automated scans are not accessibility certification.
- Capture the remaining workflow screenshots after isolated governed demo fixtures exist.
- Run a container vulnerability scanner and complete a focused human security review of the final
  diff.

## Optional future work

Controlled import/export, approved-source ingestion, maps/geospatial search, a real-data pilot,
public beta, and national coverage are optional after portfolio listing and must not be represented as
completed.

