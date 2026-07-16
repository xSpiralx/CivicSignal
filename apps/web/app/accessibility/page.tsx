export default function AccessibilityPage() {
  return (
    <main id="main-content" className="mx-auto max-w-3xl px-5 py-16 sm:px-8">
      <article className="glass rounded-[2rem] p-7 sm:p-10">
        <p className="eyebrow">Accessibility</p>
        <h1 className="mt-3 text-4xl font-extrabold">
          Useful by more people, in more situations.
        </h1>
        <p className="mt-5 text-lg text-[var(--muted)]">
          CivicSignal targets WCAG 2.2 AA-oriented practices including semantic
          structure, keyboard access, visible focus, touch-friendly controls,
          reduced motion, and reduced transparency. This is not a formal
          compliance claim.
        </p>
        <p className="mt-5">
          Accessibility feedback is welcome through the public project
          repository without including personal crisis details.
        </p>
      </article>
    </main>
  );
}
