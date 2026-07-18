# Release-candidate risk register

| Priority | Class          | Finding                                                                 | Disposition                                                     |
| -------: | -------------- | ----------------------------------------------------------------------- | --------------------------------------------------------------- |
|       P1 | Security       | Correction limiter is process-local                                     | Add shared edge/datastore limiter before multi-instance beta    |
|       P1 | Accessibility  | Correction/re-verification manual and browser review incomplete         | Block beta pending automated and manual review                  |
|       P0 | Security       | No controlled import/ingestion or SSRF boundary                         | Block beta; build allowlisted job systems and adversarial tests |
|       P0 | Reliability    | No verified restore or alert path                                       | Block beta pending provider drill and tested destination        |
|       P0 | Data integrity | No approved real-data pilot                                             | Block beta pending owner/source approval                        |
|       P1 | Accessibility  | Dialog component checks pass; page-level and manual review remain       | Add automation and manual keyboard/screen-reader review         |
|       P1 | Reliability    | Review/verification UI exists but isolated browser tests are incomplete | Complete Docker-backed workflows before beta                    |
|       P1 | Privacy        | Location/map design not implemented                                     | Default to manual input; never persist visitor coordinates      |
|       P2 | Performance    | No measured load baseline                                               | Add bounded staging tests after required endpoints exist        |

Intermittent local first-start health failures were reproduced and fixed by using IPv4 for the web
probe and a realistic API timeout. Local port collisions are handled through ignored `.env` values.
