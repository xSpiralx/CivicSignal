import type { Metadata } from "next";

export const metadata: Metadata = { title: "Verification | CivicSignal" };

export default function VerificationPage() {
  return (
    <main id="main-content" className="mx-auto max-w-4xl px-5 py-16 sm:px-8">
      <article className="glass rounded-[2rem] p-7 sm:p-10">
        <p className="eyebrow">Verification</p>
        <h1 className="mt-3 text-4xl font-extrabold">
          A recorded check, not a guarantee.
        </h1>
        <p className="mt-5 text-lg text-[var(--muted)]">
          “Verified” means a named reviewer checked required facts against cited
          official evidence on the displayed date, recorded an outcome, and set
          a next review date. It does not guarantee availability, eligibility,
          quality, safety, or a successful application.
        </p>
        <ol className="mt-8 grid gap-4 sm:grid-cols-3">
          <li className="rounded-2xl border border-white/80 bg-white/50 p-5">
            <strong>1. Draft</strong>
            <p className="mt-2 text-sm text-[var(--muted)]">
              Imported and provider-submitted facts enter a private governed
              draft.
            </p>
          </li>
          <li className="rounded-2xl border border-white/80 bg-white/50 p-5">
            <strong>2. Human review</strong>
            <p className="mt-2 text-sm text-[var(--muted)]">
              A reviewer checks source, scope, contacts, hours, eligibility,
              cost, and risk.
            </p>
          </li>
          <li className="rounded-2xl border border-white/80 bg-white/50 p-5">
            <strong>3. Publication</strong>
            <p className="mt-2 text-sm text-[var(--muted)]">
              Only a separately authorized publication decision changes the
              public listing.
            </p>
          </li>
        </ol>
        <h2 className="mt-8 text-2xl font-bold">Freshness and corrections</h2>
        <p className="mt-2">
          Listings show fresh, review-soon, stale, or unknown context. Public
          correction reports cannot edit a listing; they create a private review
          item. Strong closure evidence can trigger immediate archival.
        </p>
        <h2 className="mt-8 text-2xl font-bold">Important limits</h2>
        <p className="mt-2">
          Confirm important details with the provider. CivicSignal is not
          emergency dispatch and does not provide medical or legal advice. Call
          911 for immediate danger.
        </p>
      </article>
    </main>
  );
}
