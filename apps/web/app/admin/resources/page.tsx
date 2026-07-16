"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AdminShell } from "@/components/admin/admin-shell";
import { GovernedResource, adminFetch } from "@/lib/admin-api";

export default function ResourcesPage() {
  return <AdminShell>{() => <Resources />}</AdminShell>;
}
function Resources() {
  const [items, setItems] = useState<GovernedResource[]>([]);
  const [state, setState] = useState("");
  const [error, setError] = useState("");
  const load = (filter = state) =>
    adminFetch<GovernedResource[]>(
      `resources${filter ? `?state=${filter}` : ""}`,
    )
      .then(setItems)
      .catch((e) => setError(e.message));
  useEffect(() => {
    void adminFetch<GovernedResource[]>("resources")
      .then(setItems)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <section className="glass rounded-3xl p-5 sm:p-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Governed directory</p>
          <h1 className="mt-2 text-3xl font-extrabold">Resource work</h1>
        </div>
        <Link
          className="rounded-full bg-[#176d83] px-4 py-2 font-bold text-white"
          href="/admin/resources/new"
        >
          New draft
        </Link>
      </div>
      <div className="mt-6 flex flex-wrap gap-2">
        <label className="font-bold" htmlFor="state-filter">
          State{" "}
        </label>
        <select
          className="rounded-xl border bg-white px-3 py-2"
          id="state-filter"
          onChange={(e) => {
            setState(e.target.value);
            void load(e.target.value);
          }}
          value={state}
        >
          <option value="">All</option>
          {[
            "draft",
            "submitted",
            "changes_requested",
            "pending_verification",
            "verified",
            "published",
            "needs_reverification",
            "rejected",
            "archived",
          ].map((item) => (
            <option key={item}>{item}</option>
          ))}
        </select>
      </div>
      {error && <p role="alert">{error}</p>}
      <div className="mt-6 grid gap-3">
        {items.map((item) => (
          <Link
            className="rounded-2xl bg-white/75 p-4"
            href={`/admin/resources/${item.id}`}
            key={item.id}
          >
            <span className="font-bold">{item.content.service_name}</span>
            <span className="mt-1 block text-sm text-[var(--muted)]">
              {item.content.organization_name} ·{" "}
              {item.state.replaceAll("_", " ")} · revision {item.revision}
            </span>
          </Link>
        ))}
        {items.length === 0 && (
          <p className="rounded-2xl bg-white/60 p-5">
            No resources match this state.
          </p>
        )}
      </div>
    </section>
  );
}
