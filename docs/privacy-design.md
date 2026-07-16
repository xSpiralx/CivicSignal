# Privacy design

The public directory requires no account, does not persist searches, does not request precise user location, and includes no advertising, profiling, or invasive analytics. Application request logs record method, path, status, duration, and correlation ID—not query strings or bodies. Operators must confirm their infrastructure proxy follows the same rule.

## Data inventory and retention

| Class | Examples | Required? | Default retention |
| --- | --- | --- | --- |
| Public resource data | organizations, contacts, sources, verification dates | Yes | While active, then archived per operator policy; provenance history preserved |
| Operational data | status code, path, latency, correlation ID | Yes for safe operation | Recommended 30 days; operator-configurable |
| Optional telemetry | aggregate metrics and error tracking | No | Off until configured; minimize and document |
| Administrator data | identity and review actions | Future administration only | Define before collection; retain audit links lawfully |
| Future user submissions | corrections or suggested resources | Not implemented | No collection until consent, retention, and deletion policy exists |

Backups inherit database retention and must be encrypted, access-controlled, tested, expired, and destroyed on schedule. Searches and precise coordinates must not be added to analytics by default. Production operators are responsible for publishing jurisdiction-appropriate retention and privacy terms.

## Draft public privacy notice

CivicSignal lets visitors browse public community-resource records without creating an account. CivicSignal does not intentionally store searches, precise visitor location, advertising identifiers, or user profiles. Servers may process limited technical data needed for reliability and abuse prevention. Resource records and their public sources are displayed to explain provenance. A self-hosted operator controls its deployment and must identify itself, its contact method, retention practices, and applicable rights. Do not submit personal crisis information through project support channels.
