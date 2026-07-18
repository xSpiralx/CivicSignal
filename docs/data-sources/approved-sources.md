# Approved-source registry

Reviewed 2026-07-18. This is an engineering and governance review, not legal advice.

## Current decision

**Automated sources approved and enabled: 0.** No automated ingestion may run. The repository includes a controlled import path, but every reviewed public source remains restricted, rejected, or under review until a named human records permission and technical approval in the database registry.

| Stable identifier | Publisher | Scope | Method | Decision | Reason |
| --- | --- | --- | --- | --- | --- |
| `hrsa-health-center-sites-2026` | U.S. Health Resources and Services Administration | Nationwide and U.S. territories | One reviewed CSV snapshot | Under review | HRSA lists usage limitations as none and updated the source on 2026-07-18. A factual projection of 18,953 active 2026 rows is staged locally in 38 bounded files, but no source approval, database import, verification, or publication is being attributed to a human yet. |
| `plymouth-ma-municipal-pages` | Town of Plymouth | Plymouth | Manual factual collection only | Under review | Official facts are useful and robots permits ordinary pages, but no sufficiently explicit general reuse/automation license was located. |
| `massgov-program-pages` | Commonwealth of Massachusetts | Statewide | Manual factual collection only | Restricted | Government facts may be reusable, but Commonwealth copyright guidance and third-party material require page-specific review. No automated copy is approved. |
| `data-gov-catalog-api` | U.S. General Services Administration | National catalog metadata | API | Under review | Catalog metadata is not itself a complete nationwide community-service inventory; each discovered dataset still needs its own license, schema, safety, and quality review. |
| `mass-211-directory` | Mass 211 | Massachusetts | None | Rejected | Public visibility is not a license to redistribute the directory; no explicit permission was obtained. |
| `findhelp-directory` | Findhelp | Commercial directory | None | Rejected | Proprietary collection; no licensed API or permission supplied. |
| `consumer-map-directories` | Google, Yelp, Facebook | Commercial directories | None | Rejected | Terms and database rights do not permit copying into CivicSignal without a licensed API and approved use. |

Machine-readable details, including caching, modification, freshness, attribution, and automation decisions, are in [`reviews/source-reviews.json`](reviews/source-reviews.json).
The geographic expansion and coverage rules are in [`nationwide-expansion.md`](nationwide-expansion.md).

## Candidate review queue

The HRSA snapshot evidence is recorded in [`proposals/hrsa-health-centers-2026.json`](proposals/hrsa-health-centers-2026.json). The existing Plymouth and Massachusetts pages in [`plymouth-candidate-review-queue.json`](plymouth-candidate-review-queue.json) are one regional research batch, not the product's geographic boundary and not a claim of coverage. None of these records are **verified, imported, or published**. Nationwide expansion requires separate approval and record review for each federal, tribal, state, territorial, county, municipal, or provider source.
