# Self-hosting

Use `compose.production.yaml` as a production-oriented example, not a complete security guarantee. Copy `.env.production.example`, inject secrets through the platform or protected secret files, and never commit the resulting file. PostgreSQL is not published to the host. Terminate TLS with a reviewed reverse proxy or load balancer and restrict the API network as appropriate.

## Backup and restore

Create encrypted backups on a separate failure domain:

```bash
docker compose -f compose.production.yaml exec -T db pg_dump -U civicsignal -Fc civicsignal > civicsignal.dump
docker compose -f compose.production.yaml exec -T db pg_restore -U civicsignal -d civicsignal --clean --if-exists < civicsignal.dump
```

Shell redirection exposes the backup to local filesystem permissions; protect and encrypt it. Test restores regularly in an isolated database.

## Upgrade

Back up, read `CHANGELOG.md`, pull the chosen signed/tagged version, build images, run `alembic upgrade head` as a one-off job, restart, and verify health and a representative resource. Keep the previous images and database backup for rollback. Database downgrade is not automatically safe after new writes; prefer restoring the compatible backup.

External PostgreSQL is supported by setting `DATABASE_URL` and omitting the bundled `db` service in an operator-maintained override. Core operation has no CivicSignal cloud dependency. Branding and emergency text use environment configuration; a fuller branding schema remains future work.
