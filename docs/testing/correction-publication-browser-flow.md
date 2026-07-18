# Correction-to-publication browser validation

The target local URLs are `http://localhost:3001` and `http://localhost:8001/docs`. Use the
configured, ignored `.env`; do not copy `.env.example` over it.

```bash
cd /Users/robb/Documents/GitHub/CivicSignal
docker compose up --build -d
docker compose exec api civicsignal-seed
```

The required isolated scenario is: view a fictional public resource, report an incorrect field,
triage and escalate as a reviewer, claim the re-verification task as a verifier, save a proposed
immutable revision with source evidence, review the comparison, publish through the confirmation
dialog, and verify both the public change and prior-revision preservation. Public data must remain
unchanged until publication. Additional scenarios cover confirm-unchanged, stale-write conflict,
expired session, forbidden action, and mobile layouts.

This checkpoint did not run those browser scenarios. Docker Desktop could not start while the host
volume had about 1.2 GiB free, and the repository does not yet have dedicated reviewer/verifier
browser fixtures or reset automation. Backend integration tests and frontend component tests cover
the non-destructive publication core, conflict handling, editor behavior, and dialog keyboard
behavior. Do not interpret those as end-to-end browser coverage.
