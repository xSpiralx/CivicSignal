import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Data sources | CivicSignal" };

export default function DataSourcesPage() {
  return (
    <main id="main-content" className="mx-auto max-w-4xl px-5 py-16 sm:px-8">
      <article className="glass rounded-[2rem] p-7 sm:p-10">
        <p className="eyebrow">Data sources</p>
        <h1 className="mt-3 text-4xl font-extrabold">
          Public does not automatically mean reusable.
        </h1>
        <p className="mt-5 text-lg text-[var(--muted)]">
          CivicSignal records where information came from, why reuse is
          permitted, any attribution requirement, the import batch, and the
          human decisions that follow. No imported record is published
          automatically.
        </p>
        <h2 className="mt-8 text-2xl font-bold">Current source status</h2>
        <p className="mt-2">
          Federal, state, territorial, tribal, county, municipal, and provider
          sources can be evaluated independently. Automated access remains
          disabled unless explicit permission, terms, hosts, and rate limits are
          approved. Approval of one source never approves every source from the
          same publisher or state.
        </p>
        <div className="mt-5 rounded-2xl border border-white/80 bg-white/50 p-5">
          <h3 className="font-bold">2026 nationwide review queue</h3>
          <p className="mt-2 text-[var(--muted)]">
            An official HRSA health-center snapshot updated in 2026 has been
            transformed into 18,953 bounded review candidates. They are not
            imported, verified, or public. A named reviewer must approve the
            source and check each record before publication.
          </p>
        </div>
        <h2 className="mt-8 text-2xl font-bold">
          What the directory does not copy
        </h2>
        <p className="mt-2">
          CivicSignal does not import proprietary directory collections,
          provider prose, personal information, or crisis case data. Sources
          with unclear rights are restricted or rejected.
        </p>
        <p className="mt-6">
          Every public detail page identifies its source and check date. See{" "}
          <Link
            className="font-bold text-[var(--teal-dark)]"
            href="/verification"
          >
            how verification works
          </Link>
          .
        </p>
      </article>
    </main>
  );
}
