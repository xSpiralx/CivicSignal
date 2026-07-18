# Nationwide coverage strategy

CivicSignal is designed for the United States as a whole: all 50 states, the District of Columbia,
and populated U.S. territories. A geographic option in the interface means “search here,” not “this
area is comprehensively covered.” Public coverage is the set of individual records that have passed
source approval, field-level review, verification, and publication.

## Expansion order

1. Review federal sources whose programs genuinely serve people nationwide or across multiple
   jurisdictions.
2. Review each state, territorial, and tribal government's open-data catalog and official program
   pages independently; approval never transfers between publishers or datasets.
3. Add county and municipal sources where rights, provenance, service area, and freshness can be
   documented.
4. Accept direct provider submissions and permissioned APIs through the same candidate-only path.
5. Publish only after a named reviewer checks location, service area, eligibility, contacts, hours,
   cost, accessibility, languages, source, verification date, and next-review date.

## Geographic data rules

- Store U.S. states and territories as USPS two-letter codes when recognized.
- Preserve city or town, postal code, country, service area, and IANA time zone separately.
- Represent statewide, territorial, multi-county, remote, and national services by explicit service
  area rather than inventing a street location.
- Never infer a user's location, demographics, eligibility, or need from a search.
- Never turn a source-level approval into automatic publication.

## Coverage reporting

Counts must come from currently public, sourced records. CivicSignal must not advertise “all towns
covered,” a percentage of the country covered, or a statewide launch without a reproducible coverage
ledger. Empty search results should direct people to nearby areas or broader terms without suggesting
that assistance does not exist.

The Plymouth/Massachusetts queue is retained as one regional research batch. It is not a pilot
boundary, a preferred state, or evidence that those records are approved.

## First nationwide 2026 staging result

On 2026-07-18, CivicSignal retrieved the official HRSA Health Center Service Delivery and Look-Alike
Sites CSV after the publisher marked the dataset updated that day and listed usage limitations as
none. The source contained 18,953 active rows carrying 2026 Data Warehouse record dates. The
preparation command projected only factual directory fields and wrote 38 files of at most 500 rows
and 900 KB each under the ignored `var/imports/hrsa-2026` review area. All 18,953 candidates pass the
governed draft schema. They remain outside PostgreSQL and outside the public site until a named human
approves the source and reviews records.
