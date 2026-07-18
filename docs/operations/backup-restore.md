# Backup and restore

Create a timestamped custom-format backup outside the repository:

```bash
mkdir -p backups
docker compose exec -T db pg_dump -U civicsignal -d civicsignal \
  --format=custom --no-owner --no-acl \
  > "backups/civicsignal-$(date -u +%Y%m%dT%H%M%SZ).dump"
```

`backups/` is ignored by Git. In production, encrypt backups, restrict access, copy them to a
separate managed store, define retention with the hosting owner, and test restores regularly. A
local file on the application host is not a production backup strategy.

Restore drills must use a disposable database, never the normal development database:

```bash
docker compose exec -T db createdb -U civicsignal civicsignal_restore_drill
docker compose exec -T db pg_restore -U civicsignal -d civicsignal_restore_drill \
  --no-owner --no-acl < backups/REPLACE.dump
docker compose exec -T \
  -e DATABASE_URL=postgresql+asyncpg://civicsignal:local-development-only@db:5432/civicsignal_restore_drill \
  api alembic current
docker compose exec -T \
  -e DATABASE_URL=postgresql+asyncpg://civicsignal:local-development-only@db:5432/civicsignal_restore_drill \
  api civicsignal resources detect-stale --dry-run
docker compose exec -T db dropdb -U civicsignal civicsignal_restore_drill
```

On 2026-07-18, a 65 KB local backup restored successfully. The restored database contained six
services, one correction, one administrator account, and four audit events; it was at Alembic head
`20260718_0006`, and application stale detection examined all six services successfully.
