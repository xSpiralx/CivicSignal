import type { Metadata } from "next";

export const metadata: Metadata = { title: "About | CivicSignal" };

export default function AboutPage() {
  return (
    <main id="main-content" className="mx-auto max-w-4xl px-5 py-16 sm:px-8">
      <article className="glass rounded-[2rem] p-7 sm:p-10">
        <p className="eyebrow">About</p>
        <h1 className="mt-3 text-4xl font-extrabold">
          Community information needs visible care.
        </h1>
        <p className="mt-5 text-lg text-[var(--muted)]">
          CivicSignal is an open-source community-resource directory designed
          around provenance, freshness, correction handling, immutable revision
          history, and human-governed publication. Its geographic model supports
          local, county, statewide, territorial, and nationwide services across
          the United States.
        </p>
        <p className="mt-5">
          The project is a limited portfolio release candidate. It does not sell
          placement, rank providers by inferred quality, save public searches,
          or replace a provider’s own guidance.
        </p>
      </article>
    </main>
  );
}
