# Public-beta release candidate

CivicSignal remains private staging software and is not a finished public service or v1.0. The
candidate work begins with automated freshness operations, but correction intake, controlled data
exchange, approved-source ingestion, geospatial discovery, monitoring, recovery validation, and
independent accessibility/security review remain mandatory blockers.

The initial pilot must be limited to one owner-approved city or county and a small category set.
Every real record requires an approved authoritative source, license/attribution, human reviewer,
human verifier, verification date, public provenance, and correction route. Fictional staging data,
test accounts, and test audit events are prohibited in beta.

No public-beta deployment has been authorized. The smallest external decisions required are pilot
geography/source approval, monitoring destination, public hostname, and explicit provider billing
approval. After engineering blockers pass, provision a separate database and accounts, restore-test
a backup, validate TLS/cookies/CSRF/rollback, and run read-only beta smoke tests before exposure.
