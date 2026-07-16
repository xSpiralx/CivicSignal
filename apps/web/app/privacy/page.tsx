export default function PrivacyPage() {
  return (
    <main id="main-content" className="mx-auto max-w-3xl px-5 py-16 sm:px-8">
      <article className="glass rounded-[2rem] p-7 sm:p-10">
        <p className="eyebrow">Privacy</p>
        <h1 className="mt-3 text-4xl font-extrabold">
          Designed to ask for less.
        </h1>
        <p className="mt-5 text-lg text-[var(--muted)]">
          Public browsing requires no account. CivicSignal does not
          intentionally save search terms, precise visitor location, advertising
          identifiers, or user profiles. Operators may process limited technical
          data needed for reliability and abuse prevention.
        </p>
        <h2 className="mt-8 text-2xl font-bold">What to avoid sharing</h2>
        <p className="mt-2">
          Do not include private medical, legal, immigration, or crisis
          information in support or correction messages.
        </p>
      </article>
    </main>
  );
}
