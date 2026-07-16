# Provider-neutral hosted architecture

Place the web and API behind TLS termination and a domain-aware reverse proxy or load balancer. Run stateless replicas from immutable images and connect the API to private managed PostgreSQL where available. Store secrets in the provider's secret manager, not image layers or public environment manifests.

Enable encrypted backups with restore tests, bounded log retention, sanitized error reporting, uptime and latency monitoring, edge/API rate limiting, request-size limits, and a reviewed Content Security Policy. Alert on elevated 5xx rates, database readiness failure, migration failure, latency, authentication anomalies once authentication exists, verification-job failure once jobs exist, and disk/database capacity.

Deploy migrations as a gated one-off step. Roll forward when possible; rollback application images only when schema compatibility is confirmed. Retain the prior image and a tested pre-migration backup. DNS, TLS, CSP, rate limiting, monitoring, retention, and incident response remain operator responsibilities.
