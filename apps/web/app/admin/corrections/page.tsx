"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { AdminShell } from "@/components/admin/admin-shell";
import { adminFetch, Correction } from "@/lib/admin-api";

export default function CorrectionsPage() {
  return <AdminShell>{() => <Queue />}</AdminShell>;
}
function Queue() {
  const [items, setItems] = useState<Correction[]>([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const load = (value = status) =>
    adminFetch<Correction[]>(`corrections${value ? `?status=${value}` : ""}`)
      .then(setItems)
      .catch((e) => setError(e.message));
  useEffect(() => {
    void adminFetch<Correction[]>("corrections")
      .then(setItems)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <section className="glass rounded-3xl p-5 sm:p-8">
      <p className="eyebrow">Trust operations</p>
      <h1 className="mt-2 text-3xl font-extrabold">Correction reports</h1>
      <p className="mt-2 text-[var(--muted)]">
        Review public reports before any directory information changes.
      </p>
      <label className="mt-6 flex max-w-xs flex-col gap-2 font-bold">
        Status
        <select
          className="rounded-xl border bg-white p-3"
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            void load(e.target.value);
          }}
        >
          <option value="">All</option>
          {[
            "new",
            "triaged",
            "needs_reverification",
            "duplicate",
            "resolved",
            "dismissed",
            "abuse",
          ].map((x) => (
            <option key={x}>{x}</option>
          ))}
        </select>
      </label>
      {error && (
        <p role="alert" className="mt-4 rounded-xl bg-red-50 p-3">
          {error}
        </p>
      )}
      <div className="mt-6 grid gap-3">
        {items.map((item) => (
          <Link
            className="rounded-2xl bg-white/75 p-4"
            href={`/admin/corrections/${item.id}`}
            key={item.id}
          >
            <strong>{item.category.replaceAll("_", " ")}</strong>
            <span className="mt-1 block text-sm text-[var(--muted)]">
              {item.status.replaceAll("_", " ")} · submitted{" "}
              {new Date(item.submitted_at).toLocaleDateString()}
            </span>
            <span className="mt-2 line-clamp-2 block">{item.description}</span>
          </Link>
        ))}
        {items.length === 0 && (
          <p className="rounded-2xl bg-white/60 p-5">
            No correction reports match this filter.
          </p>
        )}
      </div>
    </section>
  );
}
