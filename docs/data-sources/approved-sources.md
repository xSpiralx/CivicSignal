# Approved-source registry

Reviewed 2026-07-18. This is an engineering and governance review, not legal advice.

## Current decision

**Approved and enabled sources: 1.** Enabled ingestion remains bounded, administrator-initiated, private, and draft-only.

| Stable identifier | Publisher | Scope | Method | Decision | Reason |
| --- | --- | --- | --- | --- | --- |
| `hrsa-health-center-sites-2026` | U.S. Health Resources and Services Administration | Nationwide and U.S. territories | One reviewed CSV snapshot | Approved | HRSA identifies BPHC as publisher, lists usage limitations as none, reports a daily refresh cycle, and dated the current source 2026-07-16. The import retains attribution and projects only public facility facts into private review candidates. |
| `plymouth-ma-municipal-pages` | Town of Plymouth | Plymouth | Manual factual collection only | Under review | Official facts are useful and robots permits ordinary pages, but no sufficiently explicit general reuse/automation license was located. |
| `massgov-program-pages` | Commonwealth of Massachusetts | Statewide | Manual factual collection only | Restricted | Government facts may be reusable, but Commonwealth copyright guidance and third-party material require page-specific review. No automated copy is approved. |
| `data-gov-catalog-api` | U.S. General Services Administration | National catalog metadata | API | Under review | Catalog metadata is not itself a complete nationwide community-service inventory; each discovered dataset still needs its own license, schema, safety, and quality review. |
| `mass-211-directory` | Mass 211 | Massachusetts | None | Rejected | Public visibility is not a license to redistribute the directory; no explicit permission was obtained. |
| `findhelp-directory` | Findhelp | Commercial directory | None | Rejected | Proprietary collection; no licensed API or permission supplied. |
| `consumer-map-directories` | Google, Yelp, Facebook | Commercial directories | None | Rejected | Terms and database rights do not permit copying into CivicSignal without a licensed API and approved use. |

Machine-readable details, including caching, modification, freshness, attribution, and automation decisions, are in [`reviews/source-reviews.json`](reviews/source-reviews.json).
The geographic expansion and coverage rules are in [`nationwide-expansion.md`](nationwide-expansion.md).

## Candidate review queue

The HRSA snapshot evidence is recorded in [`proposals/hrsa-health-centers-2026.json`](proposals/hrsa-health-centers-2026.json). The existing Plymouth and Massachusetts pages in [`plymouth-candidate-review-queue.json`](plymouth-candidate-review-queue.json) are one regional research batch, not the product's geographic boundary and not a claim of coverage. HRSA candidates are imported privately and remain unverified and unpublished. Nationwide expansion requires separate approval and record review for every additional source.
