# Washington, DC limited real-data pilot

## Scope

This optional pilot contains five service records covering public benefits and food assistance,
homelessness day services, employment assistance, and developmental-disability intake within the
District of Columbia. It is intentionally not a complete directory, does not rank providers, and
does not claim that a listed service has capacity or that a visitor is eligible.

The records summarize facts from official District government pages. CivicSignal does not copy DC
logos or imply endorsement. District Data Catalog facts are generally offered under CC0, while the
District's terms distinguish catalog data from other website content. The pilot therefore stores
short factual summaries, contact details, and links rather than republishing page prose. Review the
[District data terms](https://dc.gov/page/terms-and-conditions-use-district-data) before expanding
the dataset.

## Human-review gate

AI-assisted research is candidate preparation, not verification. Before publishing, a named human
reviewer must open every source link in `PILOT_SERVICES` and confirm:

1. the organization and service still exist;
2. operating status, address, hours, and phone number match;
3. eligibility and appointment wording does not over-promise access;
4. language and accessibility claims are supported;
5. the link is an official `https` District source;
6. no confidential shelter address or personal information is included;
7. seasonal or emergency information has not been presented as permanent; and
8. the public banner is configured for the limited DC pilot.

After that review, load the records once:

```bash
docker compose exec api civicsignal-pilot-seed \
  --reviewer-name "FULL HUMAN NAME" \
  --acknowledge-source-review
```

The command is idempotent, records the reviewer, and gives each record a 14-day verification window.
It refuses to publish without the explicit acknowledgement. Do not put a reviewer name in source,
environment variables, CI, or a public deployment command.

Set `NEXT_PUBLIC_DATA_MODE=dc-pilot` on the web service only after the review and import. The banner
then describes the limited, incomplete coverage and directs visitors to confirm details.

## Current authoritative sources

- [DC DHS service centers](https://dhs.dc.gov/service/find-service-center-near-you)
- [DC DHS day services centers](https://dhs.dc.gov/page/day-services-centers)
- [DC DOES American Job Center](https://does.dc.gov/service/american-job-center)
- [DC DOES contact information](https://unemployment.dc.gov/page/contact-information-1)
- [DC DDS/DDA intake](https://dds.dc.gov/service/how-apply-services)
- [DC DHS SNAP](https://dhs.dc.gov/service/supplemental-nutrition-assistance-program-snap)

## Maintenance

- Recheck all records at least every 14 days and immediately after a public correction.
- Archive a record rather than guessing when an official source conflicts or disappears.
- Treat emergency, shelter-capacity, and weather information as volatile; link to the live official
  source instead of copying a temporary status.
- Never collect or infer a visitor's race, disability, immigration status, income, or household
  composition. Public filters search service eligibility, languages, accessibility, and geography.
- Keep source retrieval timestamps and correction history. Do not silently overwrite provenance.
