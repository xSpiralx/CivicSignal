export default function SecurityPage() {
  return (
    <main id="main-content" className="mx-auto max-w-3xl px-5 py-16 sm:px-8">
      <article className="glass rounded-[2rem] p-7 sm:p-10">
        <p className="eyebrow">Security</p>
        <h1 className="mt-3 text-4xl font-extrabold">
          Report concerns privately.
        </h1>
        <p className="mt-5 text-lg text-[var(--muted)]">
          Do not open a public issue for a suspected vulnerability or include
          personal crisis information. Contact the repository owner through the
          private channel documented in the project security policy.
        </p>
        <p className="mt-5">
          CivicSignal is pre-release software and does not claim complete
          security or compliance.
        </p>
      </article>
    </main>
  );
}
