"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";
import { AdminSession, adminFetch, loadSession } from "@/lib/admin-api";

export function AdminShell({
  children,
}: {
  children: (session: AdminSession) => ReactNode;
}) {
  const [session, setSession] = useState<AdminSession | null>(null);
  const [error, setError] = useState("");
  const router = useRouter();
  const pathname = usePathname();
  useEffect(() => {
    loadSession()
      .then(setSession)
      .catch((cause) =>
        cause.status === 401
          ? router.replace(`/admin/sign-in?expired=1`)
          : setError(cause.message),
      );
  }, [router]);
  if (error)
    return (
      <main className="mx-auto max-w-3xl p-6">
        <div className="glass rounded-3xl p-8">
          <h1 className="text-2xl font-bold">
            Administrator access unavailable
          </h1>
          <p className="mt-3">{error}</p>
        </div>
      </main>
    );
  if (!session)
    return (
      <main aria-busy="true" className="mx-auto max-w-3xl p-8">
        <p className="glass rounded-3xl p-8">Checking administrator access…</p>
      </main>
    );
  const links = [
    { href: "/admin", label: "Overview" },
    { href: "/admin/resources", label: "Resources" },
    { href: "/admin/sessions", label: "My sessions" },
  ];
  if (session.account.permissions.includes("correction.view"))
    links.push({ href: "/admin/corrections", label: "Corrections" });
  if (session.account.permissions.includes("reverification.view"))
    links.push({ href: "/admin/reverification", label: "Re-verification" });
  if (session.account.permissions.includes("resource.view"))
    links.push({
      href: "/admin/import-candidates",
      label: "Import candidates",
    });
  if (session.account.permissions.includes("audit.view"))
    links.push({ href: "/admin/audit", label: "Audit history" });
  if (session.account.permissions.includes("account.view"))
    links.push({ href: "/admin/accounts", label: "Accounts" });
  return (
    <div className="min-h-screen">
      <a className="skip-link" href="#admin-content">
        Skip to administrator content
      </a>
      <header className="no-print p-3 sm:p-5">
        <div className="glass mx-auto flex max-w-7xl flex-wrap items-center gap-3 rounded-3xl px-5 py-4">
          <Link className="mr-auto font-extrabold" href="/admin">
            CivicSignal <span className="text-[var(--muted)]">Admin</span>
          </Link>
          <Link href="/">Public site</Link>
          <button
            className="rounded-full bg-[#175f75] px-4 py-2 text-sm font-bold text-white"
            onClick={async () => {
              await adminFetch("auth/sign-out", { method: "POST" });
              router.replace("/admin/sign-in");
            }}
          >
            Sign out
          </button>
        </div>
      </header>
      <div className="mx-auto grid max-w-7xl gap-5 px-4 pb-10 md:grid-cols-[14rem_1fr]">
        <aside className="glass-subtle rounded-3xl p-4">
          <p className="font-bold">{session.account.display_name}</p>
          <p className="text-sm text-[var(--muted)]">
            {session.account.roles.join(", ")}
          </p>
          <nav className="mt-5 grid gap-1" aria-label="Administrator">
            <>
              {links.map((link) => (
                <Link
                  aria-current={pathname === link.href ? "page" : undefined}
                  className={`rounded-xl px-3 py-2 font-semibold ${pathname === link.href ? "bg-white" : ""}`}
                  href={link.href}
                  key={link.href}
                >
                  {link.label}
                </Link>
              ))}
            </>
          </nav>
        </aside>
        <main id="admin-content">{children(session)}</main>
      </div>
    </div>
  );
}
