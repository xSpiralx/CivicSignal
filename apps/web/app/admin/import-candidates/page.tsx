"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { AdminShell } from "@/components/admin/admin-shell";
import { ImportCandidate, adminFetch } from "@/lib/admin-api";
import { US_REGIONS } from "@/lib/us-regions";

type CandidatePage = {
  items: ImportCandidate[];
  pagination: { page: number; page_size: number; total: number; pages: number };
};
type Dashboard = {
  total: number;
  ready_for_review: number;
  high_risk: number;
  possible_duplicates: number;
  conflicts: number;
};

export default function ImportCandidatesPage() {
  const [result, setResult] = useState<CandidatePage | null>(null);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [query, setQuery] = useState(new URLSearchParams({ page_size: "25" }));
  const [error, setError] = useState("");
  const load = (params: URLSearchParams) => {
    adminFetch<CandidatePage>(`imports/candidates?${params}`)
      .then(setResult)
      .catch((cause) => setError(cause.message));
  };
  useEffect(() => {
    load(query);
    adminFetch<Dashboard>("imports/dashboard")
      .then(setDashboard)
      .catch(() => {});
  }, [query]);
  function filter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const params = new URLSearchParams({ page_size: "25" });
    for (const [key, value] of data)
      if (String(value).trim()) params.set(key, String(value).trim());
    setQuery(params);
  }
  return (
    <AdminShell>
      {() => (
        <div className="grid gap-5">
          <section className="glass rounded-3xl p-6 sm:p-8">
            <p className="eyebrow">Private nationwide intake</p>
            <h1 className="mt-2 text-3xl font-extrabold">Import candidates</h1>
            <p className="mt-3 max-w-3xl text-[var(--muted)]">
              These records are not public. Approval creates an unpublished
              governed draft that must still be verified and published
              separately.
            </p>
            <Link
              className="mt-4 inline-block rounded-full bg-white px-4 py-2 font-bold"
              href="/admin/import-candidates/coverage"
            >
              View state coverage
            </Link>
            {dashboard && (
              <dl className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                <Metric label="Total" value={dashboard.total} />
                <Metric label="Ready" value={dashboard.ready_for_review} />
                <Metric label="High risk" value={dashboard.high_risk} />
                <Metric
                  label="Duplicates"
                  value={dashboard.possible_duplicates}
                />
                <Metric label="Conflicts" value={dashboard.conflicts} />
              </dl>
            )}
          </section>
          <form
            className="glass-subtle grid gap-3 rounded-3xl p-5 sm:grid-cols-2 lg:grid-cols-4"
            onSubmit={filter}
          >
            <label className="grid gap-1 text-sm font-bold">
              Search
              <input
                className="rounded-xl border border-[#bfd0d8] bg-white px-3 py-2"
                name="q"
              />
            </label>
            <label className="grid gap-1 text-sm font-bold">
              State
              <select
                className="rounded-xl border border-[#bfd0d8] bg-white px-3 py-2"
                name="state"
              >
                <option value="">All states</option>
                {US_REGIONS.map(([code, name]) => (
                  <option key={code} value={code}>
                    {name}
                  </option>
                ))}
              </select>
            </label>
            <label className="grid gap-1 text-sm font-bold">
              City
              <input
                className="rounded-xl border border-[#bfd0d8] bg-white px-3 py-2"
                name="city"
              />
            </label>
            <label className="grid gap-1 text-sm font-bold">
              County
              <input
                className="rounded-xl border border-[#bfd0d8] bg-white px-3 py-2"
                name="county"
              />
            </label>
            <label className="grid gap-1 text-sm font-bold">
              ZIP
              <input
                className="rounded-xl border border-[#bfd0d8] bg-white px-3 py-2"
                name="postal_code"
              />
            </label>
            <label className="grid gap-1 text-sm font-bold">
              Review status
              <select
                className="rounded-xl border border-[#bfd0d8] bg-white px-3 py-2"
                name="review_status"
              >
                <option value="">All statuses</option>
                <option value="ready_for_review">Ready for review</option>
                <option value="claimed">Claimed</option>
                <option value="needs_source_review">Needs source review</option>
                <option value="needs_duplicate_review">
                  Needs duplicate review
                </option>
                <option value="deferred">Deferred</option>
                <option value="accepted_as_draft">Approved as draft</option>
                <option value="rejected">Rejected</option>
              </select>
            </label>
            <label className="grid gap-1 text-sm font-bold">
              Risk
              <select
                className="rounded-xl border border-[#bfd0d8] bg-white px-3 py-2"
                name="risk"
              >
                <option value="">All risk levels</option>
                <option value="high">High risk</option>
                <option value="standard">Standard</option>
              </select>
            </label>
            <button
              className="self-end rounded-full bg-[#175f75] px-5 py-2.5 font-bold text-white"
              type="submit"
            >
              Apply filters
            </button>
          </form>
          {error && (
            <p className="rounded-2xl bg-red-50 p-4 text-red-900" role="alert">
              {error}
            </p>
          )}
          <section className="glass rounded-3xl p-4 sm:p-6" aria-busy={!result}>
            <div className="mb-4 flex items-center justify-between gap-3">
              <h2 className="text-xl font-bold">Review queue</h2>
              <p className="text-sm text-[var(--muted)]">
                {result?.pagination.total ?? 0} candidates
              </p>
            </div>
            <div className="grid gap-3">
              {result?.items.map((item) => (
                <Link
                  className="rounded-2xl border border-[#c9dbe3] bg-white/80 p-4 transition hover:border-[#175f75]"
                  href={`/admin/import-candidates/${item.id}`}
                  key={item.id}
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <h3 className="font-bold">{item.content.service_name}</h3>
                      <p className="text-sm text-[var(--muted)]">
                        {item.content.organization_name}
                      </p>
                    </div>
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-bold ${item.risk_classification === "high" ? "bg-amber-100 text-amber-900" : "bg-sky-50 text-sky-900"}`}
                    >
                      {item.risk_classification} risk
                    </span>
                  </div>
                  <p className="mt-2 text-sm">
                    {[item.city, item.county, item.region, item.postal_code]
                      .filter(Boolean)
                      .join(", ") || "Nationwide / remote"}
                  </p>
                  <p className="mt-2 text-xs text-[var(--muted)]">
                    {item.source.name} ·{" "}
                    {item.review_status.replaceAll("_", " ")} ·{" "}
                    {item.source_record_updated_at?.slice(0, 10) ??
                      item.dataset_updated_at?.slice(0, 10)}
                  </p>
                </Link>
              ))}
              {result && result.items.length === 0 && (
                <p className="rounded-2xl bg-white/70 p-6">
                  No candidates match these filters.
                </p>
              )}
            </div>
            {result && result.pagination.pages > 1 && (
              <div className="mt-5 flex justify-between">
                <button
                  disabled={result.pagination.page <= 1}
                  onClick={() => {
                    const next = new URLSearchParams(query);
                    next.set("page", String(result.pagination.page - 1));
                    setQuery(next);
                  }}
                  className="rounded-full bg-white px-4 py-2 font-bold disabled:opacity-40"
                >
                  Previous
                </button>
                <span className="p-2 text-sm">
                  Page {result.pagination.page} of {result.pagination.pages}
                </span>
                <button
                  disabled={result.pagination.page >= result.pagination.pages}
                  onClick={() => {
                    const next = new URLSearchParams(query);
                    next.set("page", String(result.pagination.page + 1));
                    setQuery(next);
                  }}
                  className="rounded-full bg-white px-4 py-2 font-bold disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            )}
          </section>
        </div>
      )}
    </AdminShell>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl bg-white/70 p-4">
      <dt className="text-xs font-bold uppercase text-[var(--muted)]">
        {label}
      </dt>
      <dd className="mt-1 text-2xl font-extrabold">{value.toLocaleString()}</dd>
    </div>
  );
}
