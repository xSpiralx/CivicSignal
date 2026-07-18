# Correction report operations

Public visitors report a published resource at `/resources/{id}/report`. The API validates bounded
fields, requires a public target, normalizes optional email, uses a honeypot and minimum submission
time, limits network/resource submissions, and deduplicates identical reports for 24 hours. It never
changes public data. Descriptions and contact details are excluded from request logs.

Reviewers use `/admin/corrections` to claim, release, triage, dismiss, mark duplicates, or escalate.
Administrators can additionally classify abuse, assign, reopen, see optional contact, and resolve.
Every mutation requires a session, CSRF token, permission, and expected version and writes an audit
event. Escalation reuses an active task for the same resource.

The built-in limiter is process-local and intentionally temporary. A multi-instance staging/beta
deployment requires a shared edge or datastore-backed limiter. Operators should redact reporter
contact after 12 months and review descriptions for deletion/redaction after 24 months.
