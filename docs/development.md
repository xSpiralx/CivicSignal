# Development environment

1. Clone the repository and copy `.env.example` to `.env`.
2. Run `docker compose up --build -d`.
3. Run `docker compose exec api alembic upgrade head` and `docker compose exec api civicsignal-seed`.
4. Open <http://localhost:3000/resources> and <http://localhost:8000/docs>.
5. Run checks from `CONTRIBUTING.md`.
6. Stop with `docker compose down`; reset only intentionally with `docker compose down -v`.

The seed is idempotent and fictional. Native development instructions remain in `CONTRIBUTING.md`. Never point tests or seed commands at a database containing data you cannot replace.
