# Re-verification operations

Use `/admin/reverification` to claim, assign, release, start, record evidence, and complete tasks.
Supported outcomes are confirmed unchanged, updated and confirmed, could not confirm, provider or
source unavailable, resource closed, archived, escalated, and cancelled duplicate.

Confirmed-unchanged creates a new verification record and recalculates the next due date. Updated
and confirmed creates a new immutable governed revision and publishes through the existing service.
Closure/archive disables the public service while preserving revisions, verification history, task,
corrections, and audit events. Expected versions prevent stale actions.

Evidence and contact summaries are bounded and must not contain sensitive client information.
Source references are required for changed publication. Related reports are resolved only for
confirmed outcomes; other outcomes remain available for administrator review.
