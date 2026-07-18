# Correction-to-re-verification browser test

Target URLs are `http://localhost:3001` and `http://localhost:8001/docs`. Start only with:

```bash
cd /Users/robb/Documents/GitHub/CivicSignal
docker compose up --build -d
```

Do not overwrite the configured `.env`. The intended isolated scenario opens a fictional resource,
submits an incorrect-hours report, signs in as reviewer, escalates, signs in separately as verifier,
records evidence, publishes a corrected revision, and confirms the public change and audit history.
This scenario remains blocked until Docker Desktop starts reliably and dedicated reviewer/verifier
fixtures are added; backend integration coverage currently validates the non-destructive core path.
