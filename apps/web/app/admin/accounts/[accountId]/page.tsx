"use client";

import { useParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { AdminShell } from "@/components/admin/admin-shell";
import { Account, RoleInfo, SafeSession, adminFetch } from "@/lib/admin-api";

export default function AccountPage() {
  return <AdminShell>{() => <Details />}</AdminShell>;
}
function Details() {
  const { accountId } = useParams<{ accountId: string }>();
  const [account, setAccount] = useState<Account | null>(null);
  const [sessions, setSessions] = useState<SafeSession[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [roles, setRoles] = useState<RoleInfo[]>([]);
  const load = () => {
    adminFetch<Account>(`accounts/${accountId}`)
      .then(setAccount)
      .catch((e) => setError(e.message));
    adminFetch<SafeSession[]>(`accounts/${accountId}/sessions`)
      .then(setSessions)
      .catch(() => undefined);
    adminFetch<RoleInfo[]>("roles")
      .then(setRoles)
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
  async function updateProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    const data = new FormData(event.currentTarget);
    const selected = data.getAll("roles").map(String);
    try {
      const updated = await adminFetch<Account>(`accounts/${accountId}`, {
        method: "PATCH",
        body: JSON.stringify({
          display_name: data.get("display_name"),
          roles: selected,
        }),
      });
      setAccount(updated);
      setNotice(
        "Account details updated. Existing sessions were revoked because roles changed.",
      );
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Update failed");
    }
  }
  async function replacePassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    const form = event.currentTarget;
    const data = new FormData(form);
    if (data.get("password") !== data.get("confirmation")) {
      setError("Passwords do not match.");
      return;
    }
    try {
      await adminFetch(`accounts/${accountId}/password`, {
        method: "POST",
        body: JSON.stringify({ password: data.get("password") }),
      });
      form.reset();
      setNotice(
        "Password replaced. All sessions for this account were revoked.",
      );
      load();
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Password replacement failed",
      );
    }
  }
  return (
    <div className="grid gap-5">
      <section className="glass rounded-3xl p-6 sm:p-8">
        <p className="eyebrow">Administrator account</p>
        <h1 className="mt-2 text-3xl font-extrabold">{account.display_name}</h1>
        <p className="mt-1 text-[var(--muted)]">{account.email}</p>
        {error && (
          <p
            role="alert"
            className="mt-4 rounded-xl bg-red-50 p-3 text-red-900"
          >
            {error}
          </p>
        )}
        {notice && (
          <p
            role="status"
            className="mt-4 rounded-xl bg-emerald-50 p-3 text-emerald-900"
          >
            {notice}
          </p>
        )}
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
        <h2 className="text-xl font-bold">Profile and roles</h2>
        <form className="mt-5 grid gap-5" onSubmit={updateProfile}>
          <label className="grid gap-2 font-bold">
            Display name
            <input
              className="rounded-2xl border bg-white px-4 py-3"
              defaultValue={account.display_name}
              maxLength={120}
              minLength={1}
              name="display_name"
              required
            />
          </label>
          <fieldset>
            <legend className="font-bold">Assigned roles</legend>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {roles.map((role) => (
                <label className="rounded-2xl bg-white/80 p-3" key={role.name}>
                  <span className="font-bold">
                    <input
                      className="mr-2"
                      defaultChecked={account.roles.includes(role.name)}
                      name="roles"
                      type="checkbox"
                      value={role.name}
                    />
                    {role.name}
                  </span>
                  <span className="mt-1 block text-xs text-[var(--muted)]">
                    {role.permissions.join(", ")}
                  </span>
                </label>
              ))}
            </div>
          </fieldset>
          <button className="justify-self-start rounded-full bg-[#176d83] px-5 py-2 font-bold text-white">
            Save profile and roles
          </button>
        </form>
      </section>
      <section className="glass-subtle rounded-3xl p-6">
        <h2 className="text-xl font-bold">Replace password</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">
          This immediately revokes every session for the account.
        </p>
        <form className="mt-5 grid gap-4" onSubmit={replacePassword}>
          <label className="grid gap-2 font-bold">
            New password
            <input
              autoComplete="new-password"
              className="rounded-2xl border bg-white px-4 py-3"
              minLength={14}
              name="password"
              required
              type="password"
            />
          </label>
          <label className="grid gap-2 font-bold">
            Confirm new password
            <input
              autoComplete="new-password"
              className="rounded-2xl border bg-white px-4 py-3"
              minLength={14}
              name="confirmation"
              required
              type="password"
            />
          </label>
          <label className="flex gap-2 text-sm">
            <input required type="checkbox" />I understand that all active
            sessions will be revoked.
          </label>
          <button className="justify-self-start rounded-full border border-red-300 px-5 py-2 font-bold text-red-800">
            Replace password
          </button>
        </form>
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
