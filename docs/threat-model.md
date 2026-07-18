# Threat model

This living assessment is not a claim that risks are fully mitigated. Likelihood and impact are qualitative and must be reassessed for each deployment and source.

| Threat                     | Component           | Likelihood | Impact   | Existing mitigation                                               | Remaining risk                                       | Planned improvement                                |
| -------------------------- | ------------------- | ---------- | -------- | ----------------------------------------------------------------- | ---------------------------------------------------- | -------------------------------------------------- |
| Fabricated resources       | Data/API            | Medium     | Critical | Sources required; public visibility policy; fictional demo labels | Human reviewers can err                              | Approved-source registry and two-person review     |
| Stale information          | Data/UI             | High       | High     | Check/expiry dates and visible stale state                        | Provider changes before expiry                       | Automated stale detection and review queue         |
| Malicious source content   | Future ingestion/UI | Medium     | High     | No arbitrary ingestion; React escapes text                        | Reviewers may enter hostile links/text               | URL allowlist, sanitization, import quarantine     |
| Prompt injection           | Future AI           | Medium     | High     | No AI or agent execution; source content remains data             | Future feature may blur boundary                     | Isolated tools, evaluated defenses, human approval |
| Crisis-data exposure       | Logs/privacy        | Medium     | Critical | No accounts/location; paths logged without query strings          | Infrastructure may log queries                       | Proxy guidance and privacy review                  |
| Unauthorized admin changes | Future admin        | Medium     | Critical | No public writes or insecure authentication                       | Database operators retain direct access              | Mature auth, least privilege, audit events         |
| Denial of service          | API/web             | High       | High     | Query/body/page caps and timeouts                                 | No distributed rate limiter                          | Edge and API rate limiting, capacity tests         |
| Supply-chain compromise    | CI/images           | Medium     | High     | Pins, lockfile, audit, Dependabot, scanning                       | Actions use moving major tags; transitive compromise | Adopt reviewed action SHA policy and SBOM/signing  |
| Misleading confidence      | UI/API              | Medium     | High     | No percentages; dates/sources/limitations visible                 | “Verified” can still be over-trusted                 | Usability research and terminology review          |
| SQL injection              | Search/API          | Low        | High     | SQLAlchemy parameterized expressions and strict bounds            | ORM misuse in future changes                         | SAST and adversarial tests                         |
| Stored XSS                 | Public content      | Medium     | High     | React escaping; no raw HTML rendering                             | Unsafe future rendering                              | Sanitization boundary and CSP                      |
| Backup disclosure          | Operations          | Medium     | Critical | Encryption/access guidance                                        | Operator practices vary                              | Automated encrypted backup/restore runbook         |

Out of scope today but requiring design before implementation: authentication, correction intake containing personal data, source import, public API quotas, production CSP, disaster recovery objectives, and AI recommendations.
