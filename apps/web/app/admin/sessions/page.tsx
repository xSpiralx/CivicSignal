"use client";

import { useEffect, useState } from "react";
import { AdminShell } from "@/components/admin/admin-shell";
import { SafeSession, adminFetch } from "@/lib/admin-api";

export default function SessionsPage() {
  return <AdminShell>{() => <Sessions />}</AdminShell>;
}
function Sessions() {
  const [items, setItems] = useState<SafeSession[]>([]);
  const [error, setError] = useState("");
  const load = () =>
    adminFetch<SafeSession[]>("sessions")
      .then(setItems)
      .catch((e) => setError(e.message));
  useEffect(() => {
    void load();
  }, []);
  return (
    <section className="glass rounded-3xl p-6 sm:p-8">
      <p className="eyebrow">Security</p>
      <h1 className="mt-2 text-3xl font-extrabold">My sessions</h1>
      <p className="mt-2 text-[var(--muted)]">
        Revocation takes effect immediately.
      </p>
      {error && (
        <p role="alert" className="mt-4 text-red-800">
          {error}
        </p>
      )}
      <div className="mt-6 grid gap-3">
        {items.map((item) => (
          <article className="rounded-2xl bg-white/75 p-4" key={item.id}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-bold">
                  {item.current ? "Current session" : "Administrator session"}
                </p>
                <p className="text-sm text-[var(--muted)]">
                  Created {new Date(item.created_at).toLocaleString()} · Expires{" "}
                  {new Date(item.expires_at).toLocaleString()}
                </p>
              </div>
              {!item.current && (
                <button
                  className="rounded-full border border-red-300 px-4 py-2 font-bold text-red-800"
                  onClick={async () => {
                    if (!window.confirm("Revoke this session?")) return;
                    await adminFetch(`sessions/${item.id}`, {
                      method: "DELETE",
                    });
                    load();
                  }}
                >
                  Revoke
                </button>
              )}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
