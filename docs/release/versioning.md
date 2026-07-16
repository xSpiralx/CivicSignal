# Versioning policy

Use SemVer-style `MAJOR.MINOR.PATCH` with `-alpha`, `-beta`, and release-candidate suffixes before stability. During alpha, minor versions may contain breaking API or migration changes, which must be explicit in the changelog. Never reuse a published version. Database compatibility, required migration order, and rollback limitations are release notes.

Migration review checks: upgrade from the previous supported schema, upgrade from empty, downgrade where safe, backup before destructive changes, data preservation, lock/runtime impact, and application/schema compatibility. Rollback checks: previous image retained, schema compatibility confirmed, backup restorable, health and representative resource verified. Demo checks: seed repeats safely, every record says demonstration only, `.example` sources resolve only as reserved examples, filters/details work, and no real-service claim appears.
