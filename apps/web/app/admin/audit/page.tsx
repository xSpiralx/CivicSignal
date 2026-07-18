"use client";

import { useEffect, useState } from "react";
import { AdminShell } from "@/components/admin/admin-shell";
import { adminFetch, AuditEvent } from "@/lib/admin-api";

export default function AuditPage() {
  return <AdminShell>{() => <AuditHistory />}</AdminShell>;
}

function AuditHistory() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    void adminFetch<AuditEvent[]>("audit?limit=50")
      .then(setEvents)
      .catch((cause) => setError(cause.message))
      .finally(() => setLoading(false));
  }, []);
  return (
    <section className="glass rounded-3xl p-5 sm:p-8">
      <p className="eyebrow">Accountability</p>
      <h1 className="mt-2 text-3xl font-extrabold">Audit history</h1>
      <p className="mt-2 max-w-3xl text-[var(--muted)]">
        Recent security and governance actions. Audit entries are append-only
        operational context; they do not expose session tokens or reporter
        contact details.
      </p>
      {error && (
        <p role="alert" className="mt-5 rounded-2xl bg-red-50 p-4">
          {error}
        </p>
      )}
      {loading && (
        <p aria-busy="true" className="mt-5">
          Loading audit history…
        </p>
      )}
      {!loading && !error && events.length === 0 && (
        <p className="mt-5 rounded-2xl bg-white/65 p-5">
          No audit events have been recorded yet.
        </p>
      )}
      <ol className="mt-6 grid gap-3">
        {events.map((event) => (
          <li key={event.id} className="rounded-2xl bg-white/75 p-4">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <strong>
                {event.action.replaceAll("_", " ").replaceAll(".", " · ")}
              </strong>
              <time
                className="text-sm text-[var(--muted)]"
                dateTime={event.created_at}
              >
                {new Date(event.created_at).toLocaleString()}
              </time>
            </div>
            <p className="mt-2">{event.summary}</p>
            <p className="mt-1 text-sm text-[var(--muted)]">
              {event.subject_type.replaceAll("_", " ")}
            </p>
          </li>
        ))}
      </ol>
    </section>
  );
}
