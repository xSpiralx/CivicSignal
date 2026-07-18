# Public-beta release gate

Status values are `passed`, `failed`, or `blocked`. Public beta is blocked if any release-blocker
row is not passed.

| Gate | Class | Status | Evidence or requirement |
|---|---|---:|---|
| Stale detection is repeatable | Data integrity | passed | Backend deterministic/idempotency tests |
| Trusted-host tests are environment-isolated | Security | passed | Explicit test hosts in fixture |
| Full re-verification operations UI | Release blocker | blocked | Queue assignment and outcomes not built |
| Public correction reporting | Release blocker | blocked | Public and administrator flows not built |
| Controlled import and export | Release blocker | blocked | Job lifecycle and secure downloads not built |
| Approved-source ingestion and SSRF suite | Security | blocked | Fetch framework not built |
| Distance search and accessible map | Accessibility | blocked | No map/search implementation |
| Rate limiting for public writes | Security | blocked | Correction/feedback endpoints absent |
| Browser governance workflows | Reliability | blocked | Only public directory E2E exists |
| Accessibility review | Accessibility | blocked | Manual review not performed |
| High-severity security findings | Security | blocked | Independent RC review not performed |
| Monitoring and tested alerts | Reliability | blocked | Notification destination not configured |
| Encrypted backup restore drill | Reliability | blocked | Provider access required |
| Approved real-resource provenance | Data integrity | blocked | Pilot area/source not approved |
| Separate beta environment and secrets | Security | blocked | Billing/DNS/provider approval required |

No staging demo or test record may enter beta. Beta requires separate database, secrets, accounts,
backups, monitoring, and hostname. Deployment is prohibited until this checklist is fully passed and
the repository owner explicitly approves public exposure and provider cost.
