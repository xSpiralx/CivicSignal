# Contributing

Thank you for improving CivicSignal. Discuss substantial architecture, data-source, privacy, or user-safety changes with maintainers before implementation. Keep pull requests focused and explain user impact, risks, verification, and any material AI assistance.

Resource contributions require authoritative source URLs, retrieval dates, original summaries, and no claim of real-time availability. Maintainers reject fabricated, harmful, unverifiable, copied, or privacy-invasive submissions. Organizations may request correction or removal through the dedicated issue template.

## Local checks

API:

```bash
cd apps/api
ruff format --check .
ruff check .
mypy src
pytest
```

Web:

```bash
cd apps/web
npm run format
npm run lint
npm run typecheck
npm test
npm run build
npm run test:e2e
```

Infrastructure:

```bash
docker compose config --quiet
docker compose build
```

Add a migration for every schema change and include tests for meaningful behavior and failures. Never commit secrets, personal crisis information, fabricated resource data, or unsupported production/security claims. All contributions require human review; see `docs/ai-development-policy.md`.

Documentation must describe changed behavior and limitations. Security-sensitive, privacy, migration, source-policy, and dependency changes require focused review. The submitter must understand all code, including AI-assisted code, and complete the pull request disclosure.
