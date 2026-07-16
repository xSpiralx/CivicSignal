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
            <h2 className="text-xl font-bold">Access tools</h2>
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
            <h2 className="font-bold">Governance development status</h2>
            <p className="mt-2 text-[var(--muted)]">
              Resource review, verification, publication, import, export, stale
              detection, and public corrections are not available in this
              release slice.
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
