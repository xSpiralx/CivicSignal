# Stale detection

The idempotent detector examines the latest verification for each active public service. It reports
`current`, `due_soon`, `due`, `overdue`, `critically_stale`, or `unknown`. Due and older records get
one active re-verification task, transition to `needs_reverification`, and receive a system audit
event. It never deletes or archives a resource.

```bash
docker compose exec api civicsignal resources detect-stale --dry-run
docker compose exec api civicsignal resources detect-stale
docker compose exec api civicsignal resources detect-stale --at 2026-07-16T18:00:00Z
```

The Render staging cron is scheduled daily at `06:00 UTC`. PostgreSQL advisory locking permits one
active execution. A failed invocation exits nonzero for provider retry/log alerting; rerunning is
safe. Disable the cron in Render before migrations or incident investigation. Expected runtime is
under one minute for the current staging dataset; investigate any run longer than five minutes.

The structured JSON summary includes examined records, freshness counts, created/existing tasks,
transitions, and dry-run state. Alert delivery is not configured until a provider destination is
approved, so repeated-failure alerting remains a beta blocker.
