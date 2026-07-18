"use client";

import { useEffect, useState } from "react";
import { AdminShell } from "@/components/admin/admin-shell";
import { ActionDialog } from "@/components/dialogs/action-dialog";
import { SafeSession, adminFetch } from "@/lib/admin-api";

export default function SessionsPage() {
  return <AdminShell>{() => <Sessions />}</AdminShell>;
}
function Sessions() {
  const [items, setItems] = useState<SafeSession[]>([]);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<SafeSession | null>(null);
  const [loading, setLoading] = useState(false);
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
                  onClick={() => setSelected(item)}
                >
                  Revoke
                </button>
              )}
            </div>
          </article>
        ))}
      </div>
      <ActionDialog
        open={selected !== null}
        title="Revoke administrator session?"
        description="Revocation takes effect immediately and cannot be undone."
        submitLabel="Revoke session"
        destructive
        loading={loading}
        error={error}
        onClose={() => setSelected(null)}
        onSubmit={async () => {
          if (!selected) return;
          setLoading(true);
          try {
            await adminFetch(`sessions/${selected.id}`, { method: "DELETE" });
            setSelected(null);
            await load();
          } catch (e) {
            setError(e instanceof Error ? e.message : "Revocation failed");
          } finally {
            setLoading(false);
          }
        }}
      >
        <label className="flex items-start gap-3">
          <input type="checkbox" required />
          <span>I understand this session will immediately lose access.</span>
        </label>
      </ActionDialog>
    </section>
  );
}
