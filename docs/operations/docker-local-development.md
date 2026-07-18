# Docker local development

This checkout is configured for web port `3001` and API port `8001`. Preserve the ignored `.env`:
do not overwrite it with `.env.example`.

```bash
cd /Users/robb/Documents/GitHub/CivicSignal
open -a Docker
docker version
docker compose up --build -d
docker compose ps
docker compose exec api civicsignal-seed
```

Open `http://localhost:3001/resources`, `http://localhost:3001/admin/sign-in`, and
`http://localhost:8001/docs`. Stop application containers without deleting data with
`docker compose stop`; use `docker compose down` to remove containers while retaining named
volumes. Never use `down -v` unless a deliberate database reset is intended.

If the daemon is unavailable, confirm Docker Desktop is open and use its Troubleshoot > Restart
action. Check free disk space with `df -h /Users/robb`; Docker Desktop may fail when the host volume
is nearly full. Free ordinary host space or remove only confirmed-unused Docker artifacts, then
restart Docker Desktop and repeat `docker version`. Do not delete CivicSignal volumes during
recovery. At this checkpoint the host had about 1.2 GiB free and Docker validation remained blocked.
