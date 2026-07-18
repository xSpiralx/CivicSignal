# Correction publication UI checkpoint

Checkpoint name: `checkpoint/correction-publication-validation-v0.9`.

Implemented: structured proposed-revision editing, immutable saves with separate working and
published pointers, optimistic version checks, server readiness results, source provenance,
human-readable published/proposed comparison, unsaved-change warning, discard, and verified
publication. Governance, correction, session, and account actions now use a reusable accessible
dialog instead of browser-native prompts and confirms. Backend publication is transactional and
retains the prior revision.

Validated locally: Ruff, strict MyPy, 27 backend tests, ESLint, strict TypeScript, 12 frontend tests,
and the Next.js production build. The active application paths contain no `window.prompt`,
`window.confirm`, or `window.alert` calls.

Blocked: Docker daemon and container builds/health, Docker-backed PostgreSQL migration and restart
persistence checks, seed/reset and CLI checks, browser E2E, mobile browser review, automated page
accessibility scanning, and manual keyboard/VoiceOver/zoom/reduced-effects review. The host volume
reported only about 1.2 GiB free. Controlled import/export, source ingestion, geospatial discovery,
AI features, beta deployment, and a v1.0 release remain out of scope.
