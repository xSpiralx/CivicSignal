import Link from "next/link";

const repository =
  process.env.NEXT_PUBLIC_REPOSITORY_URL ??
  "https://github.com/xSpiralx/CivicSignal";

export function SiteHeader() {
  return (
    <header className="no-print sticky top-0 z-40 px-3 pt-3 sm:px-6">
      <div className="glass mx-auto flex max-w-7xl items-center justify-between rounded-[1.4rem] px-4 py-3 sm:px-6">
        <Link
          href="/"
          aria-label="CivicSignal home"
          className="flex items-center gap-3 font-extrabold tracking-tight"
        >
          <span
            aria-hidden="true"
            className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-[#137e97] to-[#296ee5] text-white shadow-lg"
          >
            C
          </span>
          <span>CivicSignal</span>
        </Link>
        <nav
          aria-label="Primary navigation"
          className="flex items-center gap-1 text-sm font-semibold"
        >
          <Link
            className="rounded-full px-3 py-2 hover:bg-white/70"
            href="/resources"
          >
            Find resources
          </Link>
          <a
            className="hidden rounded-full px-3 py-2 hover:bg-white/70 sm:block"
            href={repository}
            rel="noreferrer"
          >
            Open source
          </a>
        </nav>
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="no-print mx-auto mt-16 max-w-7xl px-5 pb-8 sm:px-8">
      <div className="glass-subtle grid gap-6 rounded-[1.75rem] p-6 text-sm sm:grid-cols-[1fr_auto]">
        <div>
          <p className="font-bold">CivicSignal</p>
          <p className="mt-1 max-w-xl text-[var(--muted)]">
            Open, privacy-minded software for clearer community resource
            information. Human review remains responsible for every published
            record.
          </p>
        </div>
        <nav
          aria-label="Footer navigation"
          className="grid grid-cols-2 gap-x-6 gap-y-2 font-semibold"
        >
          <a href="/privacy">Privacy</a>
          <a href="/security">Security</a>
          <a href="/accessibility">Accessibility</a>
          <a href={repository}>Contribute</a>
        </nav>
      </div>
      <p className="mt-4 text-center text-xs text-[var(--muted)]">
        Portfolio-stage release candidate · Fictional data · Apache-2.0
      </p>
    </footer>
  );
}
