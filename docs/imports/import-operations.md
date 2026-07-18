# Import operations

1. Register and approve a source after license and technical review.
2. Prepare a bounded snapshot and inspect its manifest and hash.
3. Dry-run each file with `civicsignal imports run` without `--commit`.
4. Commit review-sized files with `--commit`; rerunning an identical payload returns its existing batch.
5. Inspect `civicsignal imports summarize` and the private administrator dashboard.
6. Pause on serious errors, storage warnings, anomalous duplicate rates, or source drift.

Never overwrite `.env`, bulk approve high-risk candidates, or publish from the import command.
