import Link from "next/link";
import { HealthStatus } from "@/components/health-status";

const categories = [
  ["Food assistance", "food-assistance"],
  ["Housing support", "housing-assistance"],
  ["Transportation", "transportation"],
  ["Healthcare access", "healthcare-access"],
  ["Child and family", "child-family"],
  ["Legal assistance", "legal-assistance"],
];

const repository =
  process.env.NEXT_PUBLIC_REPOSITORY_URL ??
  "https://github.com/xSpiralx/CivicSignal";

export default function Home() {
  return (
    <main id="main-content">
      <section className="mx-auto max-w-7xl px-5 pb-16 pt-12 sm:px-8 sm:pt-20">
        <div className="grid items-center gap-10 lg:grid-cols-[1.08fr_.92fr]">
          <div>
            <p className="eyebrow">Trusted help, clearly sourced</p>
            <h1 className="text-balance mt-4 max-w-4xl text-5xl font-extrabold leading-[1.02] tracking-[-.045em] sm:text-7xl">
              Find community support with clarity and care.
            </h1>
            <p className="mt-6 max-w-2xl text-lg text-[var(--muted)] sm:text-xl">
              Search a public directory that shows where information came from,
              when it was checked, and when you should confirm details directly.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/resources"
                className="liquid-button min-h-12 rounded-full bg-gradient-to-b from-[#2987eb] to-[#1767cf] px-6 py-3 font-bold text-white"
              >
                Search community resources
              </Link>
              <a
                href="#how-verification-works"
                className="glass-subtle min-h-12 rounded-full px-6 py-3 font-bold"
              >
                How verification works
              </a>
            </div>
            <div className="mt-7 flex items-center gap-3 text-sm text-[var(--muted)]">
              <span
                aria-hidden="true"
                className="h-2.5 w-2.5 rounded-full bg-emerald-600 shadow-[0_0_0_5px_rgba(5,150,105,.12)]"
              />
              <HealthStatus />
            </div>
          </div>
          <aside
            aria-labelledby="emergency-heading"
            className="glass relative overflow-hidden rounded-[2.3rem] p-7 sm:p-9"
          >
            <div
              aria-hidden="true"
              className="absolute -right-16 -top-16 h-48 w-48 rounded-full bg-gradient-to-br from-cyan-200/70 to-blue-300/20 blur-2xl"
            />
            <p className="eyebrow">Important</p>
            <h2 id="emergency-heading" className="mt-3 text-2xl font-extrabold">
              Immediate danger?
            </h2>
            <p className="mt-3 text-xl font-bold text-[var(--urgent)]">
              Call 911 for immediate danger.
            </p>
            <p className="mt-4 text-[var(--muted)]">
              CivicSignal does not replace emergency services or professional
              advice, and cannot guarantee current availability.
            </p>
            <div className="mt-7 rounded-2xl border border-white/80 bg-white/55 p-4 text-sm">
              <strong>Privacy by default</strong>
              <p className="mt-1 text-[var(--muted)]">
                No account required. Searches are not saved by CivicSignal.
              </p>
            </div>
          </aside>
        </div>
      </section>
      <section
        aria-labelledby="browse-heading"
        className="mx-auto max-w-7xl px-5 py-10 sm:px-8"
      >
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="eyebrow">Browse by need</p>
            <h2
              id="browse-heading"
              className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl"
            >
              A calmer place to begin
            </h2>
          </div>
          <Link href="/resources" className="font-bold text-[var(--teal-dark)]">
            View every category →
          </Link>
        </div>
        <div className="mt-7 grid grid-cols-2 gap-3 md:grid-cols-3">
          {categories.map(([category, slug], index) => (
            <Link
              key={category}
              href={`/resources?category=${slug}`}
              className="glass-subtle group min-h-28 rounded-[1.5rem] p-5 font-bold transition hover:-translate-y-1"
            >
              <span
                aria-hidden="true"
                className={`mb-4 block h-8 w-8 rounded-xl bg-gradient-to-br ${index % 3 === 0 ? "from-cyan-300 to-blue-500" : index % 3 === 1 ? "from-violet-300 to-indigo-500" : "from-emerald-300 to-teal-600"} shadow-sm`}
              />
              {category}
              <span className="float-right opacity-0 transition group-hover:opacity-100">
                ↗
              </span>
            </Link>
          ))}
        </div>
      </section>
      <section
        id="how-verification-works"
        aria-labelledby="verification-heading"
        className="mx-auto max-w-7xl px-5 py-14 sm:px-8"
      >
        <div className="glass overflow-hidden rounded-[2.4rem] p-7 sm:p-10">
          <div className="grid gap-10 lg:grid-cols-[.8fr_1.2fr]">
            <div>
              <p className="eyebrow">Trust is a process</p>
              <h2
                id="verification-heading"
                className="text-balance mt-3 text-3xl font-extrabold sm:text-4xl"
              >
                Useful context, not a confidence score.
              </h2>
              <p className="mt-4 text-[var(--muted)]">
                Every public record needs a source and a review state. We show
                dates and warnings so you can make an informed call.
              </p>
            </div>
            <ol className="grid gap-3 sm:grid-cols-3">
              {[
                [
                  "01",
                  "Source attached",
                  "A public reference explains where the information came from.",
                ],
                [
                  "02",
                  "Human checked",
                  "A reviewer records what was checked and when.",
                ],
                [
                  "03",
                  "Freshness shown",
                  "Older information stays visible only with a clear warning policy.",
                ],
              ].map(([number, title, copy]) => (
                <li
                  key={number}
                  className="rounded-2xl border border-white/80 bg-white/50 p-5"
                >
                  <span className="text-xs font-black text-[var(--blue)]">
                    {number}
                  </span>
                  <h3 className="mt-3 font-extrabold">{title}</h3>
                  <p className="mt-2 text-sm text-[var(--muted)]">{copy}</p>
                </li>
              ))}
            </ol>
          </div>
        </div>
      </section>
      <section
        id="about-project"
        aria-labelledby="about-project-heading"
        className="mx-auto max-w-7xl px-5 py-12 sm:px-8"
      >
        <div className="mb-5 grid gap-5 lg:grid-cols-3">
          <article className="glass-subtle rounded-[1.8rem] p-7 lg:col-span-2">
            <p className="eyebrow">Why CivicSignal exists</p>
            <h2
              id="about-project-heading"
              className="mt-2 text-2xl font-extrabold"
            >
              Community information changes. Trust needs a visible process.
            </h2>
            <p className="mt-3 text-[var(--muted)]">
              CivicSignal demonstrates how public corrections can move through
              human triage, re-verification, an immutable proposed revision, and
              audited publication without silently rewriting history.
            </p>
          </article>
          <article className="glass-subtle rounded-[1.8rem] p-7">
            <p className="eyebrow">Privacy + access</p>
            <h2 className="mt-2 text-2xl font-extrabold">
              Designed intentionally.
            </h2>
            <p className="mt-3 text-[var(--muted)]">
              Search requires no account, visitor queries are not retained, and
              public and administrator workflows use semantic, keyboard-friendly
              controls.
            </p>
          </article>
        </div>
        <div className="grid gap-5 md:grid-cols-2">
          <article className="glass-subtle rounded-[1.8rem] p-7">
            <p className="eyebrow">Open source</p>
            <h2 className="mt-2 text-2xl font-extrabold">
              Built in public, improved together.
            </h2>
            <p className="mt-3 text-[var(--muted)]">
              Inspect the architecture, report incorrect information, or help
              improve the project. AI-assisted work is disclosed and
              human-reviewed.
            </p>
            <a
              href={repository}
              className="mt-5 inline-block font-bold text-[var(--teal-dark)]"
            >
              Explore the repository →
            </a>
          </article>
          <article className="glass-subtle rounded-[1.8rem] p-7">
            <p className="eyebrow">Information needs care</p>
            <h2 className="mt-2 text-2xl font-extrabold">
              See something that changed?
            </h2>
            <p className="mt-3 text-[var(--muted)]">
              Phone numbers, hours, and eligibility can change. Correction
              reports never modify listings automatically.
            </p>
            <Link
              href="/resources"
              className="mt-5 inline-block font-bold text-[var(--teal-dark)]"
            >
              Report incorrect information →
            </Link>
          </article>
        </div>
      </section>
    </main>
  );
}
