# Nationwide import architecture

Approved source → bounded parser → freshness gate → normalization → explainable duplicate/conflict checks → idempotent import batch → private candidate queue → human approval as governed draft → existing verification → existing publication.

Import batches use payload hashes, idempotency keys, checkpoints, resume tokens, per-file transactions, error summaries, and cancellation state. Candidate fields used by filters are indexed separately from the immutable normalized and retained source projections. Large sources are split into at most 500 records and 900 KB per file; public queries never join candidate tables.
