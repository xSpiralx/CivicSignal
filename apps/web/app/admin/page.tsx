"use client";

import Link from "next/link";
import { AdminShell } from "@/components/admin/admin-shell";

export default function AdminPage() {
  return (
    <AdminShell>
      {(session) => (
        <div className="grid gap-5">
          <section className="glass rounded-3xl p-6 sm:p-8">
            <p className="eyebrow">Administrator overview</p>
            <h1 className="mt-2 text-3xl font-extrabold">
              Welcome, {session.account.display_name}
            </h1>
            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              <Info
                label="Account status"
                value={session.account.is_active ? "Active" : "Disabled"}
              />
              <Info label="Roles" value={session.account.roles.join(", ")} />
              <Info
                label="Session began"
                value={new Date(session.created_at).toLocaleString()}
              />
              <Info
                label="Session expires"
                value={new Date(session.expires_at).toLocaleString()}
              />
            </div>
          </section>
          <section className="glass-subtle rounded-3xl p-6">
            <h2 className="text-xl font-bold">Guided demonstration</h2>
            <ol className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
              <li className="rounded-2xl bg-white/70 p-4">
                <strong>1. Review</strong>
                <br />
                Open a submitted correction and record triage.
              </li>
              <li className="rounded-2xl bg-white/70 p-4">
                <strong>2. Re-verify</strong>
                <br />
                Escalate and claim the resulting task.
              </li>
              <li className="rounded-2xl bg-white/70 p-4">
                <strong>3. Propose</strong>
                <br />
                Edit an immutable revision and review readiness.
              </li>
              <li className="rounded-2xl bg-white/70 p-4">
                <strong>4. Publish</strong>
                <br />
                Confirm evidence, publish, and inspect the public result.
              </li>
            </ol>
            <h2 className="mt-7 text-xl font-bold">Access tools</h2>
            <div className="mt-4 flex flex-wrap gap-3">
              <Link
                className="rounded-full bg-white px-4 py-2 font-bold"
                href="/admin/sessions"
              >
                Manage my sessions
              </Link>
              {session.account.permissions.includes("account.view") && (
                <Link
                  className="rounded-full bg-white px-4 py-2 font-bold"
                  href="/admin/accounts"
                >
                  Manage accounts
                </Link>
              )}
            </div>
          </section>
          <section className="rounded-3xl border border-[#c9dbe3] bg-white/75 p-6">
            <h2 className="font-bold">Portfolio demonstration status</h2>
            <p className="mt-2 text-[var(--muted)]">
              Resource governance, public corrections, re-verification,
              immutable proposed revisions, audited publication, and stale
              detection are available. All records in this environment are
              fictional.
            </p>
          </section>
        </div>
      )}
    </AdminShell>
  );
}
function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-white/70 p-4">
      <dt className="text-sm font-bold text-[var(--muted)]">{label}</dt>
      <dd className="mt-1 font-semibold">{value}</dd>
    </div>
  );
}
