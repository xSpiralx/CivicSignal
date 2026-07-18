# Development environment

1. Configure an ignored `.env` once. Do not replace it with `.env.example` after configuration.
   This checkout uses `WEB_PORT=3001` and `API_PORT=8001`.
2. Run `cd /Users/robb/Documents/GitHub/CivicSignal && docker compose up --build -d`.
3. Run `docker compose exec api alembic upgrade head` and `docker compose exec api civicsignal-seed`.
4. Open <http://localhost:3001/resources>, <http://localhost:3001/admin/sign-in>, and <http://localhost:8001/docs>.
5. Run checks from `CONTRIBUTING.md`.
6. Stop with `docker compose down`; reset only intentionally with `docker compose down -v`.

The seed is idempotent and fictional. Native development instructions remain in `CONTRIBUTING.md`. Never point tests or seed commands at a database containing data you cannot replace.
