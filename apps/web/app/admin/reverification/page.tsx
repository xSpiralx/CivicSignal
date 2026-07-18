"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { AdminShell } from "@/components/admin/admin-shell";
import { adminFetch, ReverificationTask } from "@/lib/admin-api";
export default function Page() {
  return <AdminShell>{() => <Queue />}</AdminShell>;
}
function Queue() {
  const [items, setItems] = useState<ReverificationTask[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    void adminFetch<ReverificationTask[]>("reverification")
      .then(setItems)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <section className="glass rounded-3xl p-5 sm:p-8">
      <p className="eyebrow">Verification operations</p>
      <h1 className="mt-2 text-3xl font-extrabold">Re-verification queue</h1>
      {error && <p role="alert">{error}</p>}
      <div className="mt-6 grid gap-3">
        {items.map((x) => (
          <Link
            className="rounded-2xl bg-white/75 p-4"
            href={`/admin/reverification/${x.id}`}
            key={x.id}
          >
            <strong>{x.reason.replaceAll("_", " ")}</strong>
            <span className="block text-sm text-[var(--muted)]">
              {x.status.replaceAll("_", " ")} ·{" "}
              {x.freshness_state.replaceAll("_", " ")} · due{" "}
              {new Date(x.due_at).toLocaleDateString()}
            </span>
          </Link>
        ))}
        {items.length === 0 && (
          <p>No active or historical re-verification tasks.</p>
        )}
      </div>
    </section>
  );
}
