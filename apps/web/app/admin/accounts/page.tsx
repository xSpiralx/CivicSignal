"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AdminShell } from "@/components/admin/admin-shell";
import { Account, adminFetch } from "@/lib/admin-api";

export default function AccountsPage() {
  return <AdminShell>{() => <Accounts />}</AdminShell>;
}
function Accounts() {
  const [items, setItems] = useState<Account[]>([]);
  const [error, setError] = useState("");
  const [q, setQ] = useState("");
  const load = () =>
    adminFetch<Account[]>(`accounts${q ? `?q=${encodeURIComponent(q)}` : ""}`)
      .then(setItems)
      .catch((e) => setError(e.message));
  useEffect(() => {
    void adminFetch<Account[]>("accounts")
      .then(setItems)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <section className="glass rounded-3xl p-5 sm:p-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Access control</p>
          <h1 className="mt-2 text-3xl font-extrabold">
            Administrator accounts
          </h1>
        </div>
        <Link
          className="rounded-full bg-[#176d83] px-4 py-2 font-bold text-white"
          href="/admin/accounts/new"
        >
          Create account
        </Link>
      </div>
      <form
        className="mt-6 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          load();
        }}
      >
        <label className="sr-only" htmlFor="account-search">
          Search accounts
        </label>
        <input
          className="min-w-0 flex-1 rounded-2xl border bg-white px-4 py-3"
          id="account-search"
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search name or email"
        />
        <button className="rounded-2xl bg-white px-4 font-bold">Search</button>
      </form>
      {error && <p role="alert">{error}</p>}
      <div className="mt-5 overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr>
              <th className="p-3">Account</th>
              <th className="p-3">Roles</th>
              <th className="p-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr className="border-t border-[#d7e3e8]" key={item.id}>
                <td className="p-3">
                  <Link
                    className="font-bold"
                    href={`/admin/accounts/${item.id}`}
                  >
                    {item.display_name}
                  </Link>
                  <br />
                  <span className="text-sm text-[var(--muted)]">
                    {item.email}
                  </span>
                </td>
                <td className="p-3">{item.roles.join(", ")}</td>
                <td className="p-3">
                  {item.is_active ? "Active" : "Disabled"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && (
          <p className="p-5 text-center text-[var(--muted)]">
            No accounts found.
          </p>
        )}
      </div>
    </section>
  );
}
