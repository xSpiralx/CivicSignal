# Import security review

Source retrieval requires HTTPS, a per-source hostname allowlist, public DNS answers before and after the request, peer-IP validation, standard port 443, bounded redirects, strict timeouts, rate limiting, approved MIME types, and streaming response limits. Private, loopback, link-local, multicast, reserved, and cloud-metadata destinations are rejected.

Parsers enforce UTF-8, file-name safety, byte/row/column/scalar/depth bounds, duplicate JSON-key rejection, CSV shape validation, and spreadsheet-formula rejection. XML and archives are not accepted. Candidate fields are rendered as React text; HTML is not trusted. SQLAlchemy parameterization, RBAC, HTTP-only sessions, CSRF, optimistic versions, and audit events protect review actions.
