"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AdminShell } from "@/components/admin/admin-shell";
import { Account, SafeSession, adminFetch } from "@/lib/admin-api";

export default function AccountPage() {
  return <AdminShell>{() => <Details />}</AdminShell>;
}
function Details() {
  const { accountId } = useParams<{ accountId: string }>();
  const [account, setAccount] = useState<Account | null>(null);
  const [sessions, setSessions] = useState<SafeSession[]>([]);
  const [error, setError] = useState("");
  const load = () => {
    adminFetch<Account>(`accounts/${accountId}`)
      .then(setAccount)
      .catch((e) => setError(e.message));
    adminFetch<SafeSession[]>(`accounts/${accountId}/sessions`)
      .then(setSessions)
      .catch(() => undefined);
  };
  useEffect(load, [accountId]);
  if (error) return <p role="alert">{error}</p>;
  if (!account) return <p aria-busy="true">Loading account…</p>;
  async function toggle() {
    if (
      !window.confirm(
        `${account?.is_active ? "Disable" : "Enable"} this account?`,
      )
    )
      return;
    await adminFetch(`accounts/${accountId}`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: !account?.is_active }),
    });
    load();
  }
  return (
    <div className="grid gap-5">
      <section className="glass rounded-3xl p-6 sm:p-8">
        <p className="eyebrow">Administrator account</p>
        <h1 className="mt-2 text-3xl font-extrabold">{account.display_name}</h1>
        <p className="mt-1 text-[var(--muted)]">{account.email}</p>
        <dl className="mt-6 grid gap-3 sm:grid-cols-2">
          <Info
            label="Status"
            value={account.is_active ? "Active" : "Disabled"}
          />
          <Info label="Roles" value={account.roles.join(", ")} />
          <Info
            label="Created"
            value={new Date(account.created_at).toLocaleString()}
          />
          <Info
            label="Last login"
            value={
              account.last_login_at
                ? new Date(account.last_login_at).toLocaleString()
                : "Never"
            }
          />
        </dl>
        <div className="mt-6 flex flex-wrap gap-3">
          <button
            className="rounded-full border border-red-300 px-4 py-2 font-bold text-red-800"
            onClick={toggle}
          >
            {account.is_active ? "Disable account" : "Enable account"}
          </button>
          <button
            className="rounded-full border px-4 py-2 font-bold"
            onClick={async () => {
              if (
                !window.confirm("Revoke every active session for this account?")
              )
                return;
              await adminFetch(`accounts/${accountId}/sessions`, {
                method: "DELETE",
              });
              load();
            }}
          >
            Revoke all sessions
          </button>
        </div>
      </section>
      <section className="glass-subtle rounded-3xl p-6">
        <h2 className="text-xl font-bold">Active sessions</h2>
        <p className="mt-2">
          {sessions.length} active session{sessions.length === 1 ? "" : "s"}
        </p>
      </section>
    </div>
  );
}
function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-white/75 p-4">
      <dt className="text-sm font-bold text-[var(--muted)]">{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}
