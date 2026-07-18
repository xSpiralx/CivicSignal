# Candidate review workflow

The queue supports state, city, county, ZIP, source, batch, status, duplicate, conflict, risk, nationwide, and remote filters with server-side pagination and stable sorting. Administrators may claim, release, assign, defer, reject, request source review, mark exact duplicates, or approve one candidate as a private draft.

Approval preserves provenance, creates revision 1 in `draft`, links the candidate, increments its optimistic version, and writes an audit event. Verification and publication remain separate existing governance decisions.
