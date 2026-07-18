# Rollback

Retain the previously healthy application images and take a database backup before deployment.
When rollback is needed, stop new administrative writes, restore the previous web/API image pair,
and roll back schema only when the prior version is confirmed compatible. Never downgrade the
normal database merely to test the procedure.

After rollback, verify API/database readiness, public resource detail, sign-in, corrections, current
migration revision, and audit logging. If data restoration is required, restore into a temporary
database first and validate it using `docs/operations/backup-restore.md`.
