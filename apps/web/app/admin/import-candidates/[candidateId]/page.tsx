"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { AdminShell } from "@/components/admin/admin-shell";
import { ImportCandidate, adminFetch } from "@/lib/admin-api";

export default function ImportCandidateDetailPage() {
  const { candidateId } = useParams<{ candidateId: string }>();
  const router = useRouter();
  const [candidate, setCandidate] = useState<ImportCandidate | null>(null);
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const load = useCallback(
    () =>
      adminFetch<ImportCandidate>(`imports/candidates/${candidateId}`)
        .then(setCandidate)
        .catch((cause) => setError(cause.message)),
    [candidateId],
  );
  useEffect(() => {
    load();
  }, [load]);
  async function action(name: string) {
    if (!candidate) return;
    setBusy(true);
    setError("");
    try {
      await adminFetch(`imports/candidates/${candidate.id}/${name}`, {
        method: "POST",
        body: JSON.stringify({
          expected_version: candidate.version,
          reason: reason || null,
        }),
      });
      await load();
      setReason("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }
  async function approve() {
    if (!candidate) return;
    if (
      candidate.risk_classification === "high" &&
      !window.confirm(
        "This is a high-risk healthcare candidate. Confirm that you reviewed its authoritative source, freshness date, and contact information before creating a private draft.",
      )
    )
      return;
    setBusy(true);
    setError("");
    try {
      const confirmed =
        candidate.risk_classification === "high"
          ? "?high_risk_confirmed=true"
          : "";
      const resource = await adminFetch<{ id: string }>(
        `imports/${candidate.batch_id}/candidates/${candidate.id}/accept${confirmed}`,
        { method: "POST" },
      );
      router.push(`/admin/resources/${resource.id}`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Approval failed");
      setBusy(false);
    }
  }
  return (
    <AdminShell>
      {() =>
        !candidate ? (
          <p className="glass rounded-3xl p-8" aria-busy={!error}>
            {error || "Loading candidate…"}
          </p>
        ) : (
          <div className="grid gap-5">
            <section className="glass rounded-3xl p-6 sm:p-8">
              <Link
                className="text-sm font-bold"
                href="/admin/import-candidates"
              >
                ← Review queue
              </Link>
              <div className="mt-5 flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="eyebrow">Private candidate</p>
                  <h1 className="mt-2 text-3xl font-extrabold">
                    {candidate.content.service_name}
                  </h1>
                  <p className="mt-2 text-[var(--muted)]">
                    {candidate.content.organization_name}
                  </p>
                </div>
                <span
                  className={`rounded-full px-4 py-2 text-sm font-bold ${candidate.risk_classification === "high" ? "bg-amber-100 text-amber-950" : "bg-sky-50 text-sky-950"}`}
                >
                  {candidate.risk_classification} risk
                </span>
              </div>
              <p className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm">
                <strong>Unpublished:</strong> approving this candidate creates a
                governed draft only. It will remain absent from public search
                until separate verification and publication.
              </p>
            </section>
            <div className="grid gap-5 lg:grid-cols-[1.35fr_.65fr]">
              <section className="glass-subtle rounded-3xl p-6">
                <h2 className="text-xl font-bold">Normalized record</h2>
                <dl className="mt-4 grid gap-4 sm:grid-cols-2">
                  <Fact
                    label="Summary"
                    value={candidate.content.description}
                    wide
                  />
                  <Fact
                    label="Location"
                    value={[
                      candidate.content.location_name,
                      candidate.city,
                      candidate.county,
                      candidate.region,
                      candidate.postal_code,
                    ]
                      .filter(Boolean)
                      .join(", ")}
                    wide
                  />
                  <Fact label="Phone" value={candidate.content.contact_phone} />
                  <Fact label="Website" value={candidate.content.website} />
                  <Fact
                    label="Service area"
                    value={candidate.content.service_area}
                  />
                  <Fact
                    label="Categories"
                    value={candidate.categories.join(", ")}
                  />
                  <Fact label="Hours" value={candidate.content.hours} wide />
                </dl>
              </section>
              <section className="glass rounded-3xl p-6">
                <h2 className="text-xl font-bold">Source and freshness</h2>
                <dl className="mt-4 grid gap-4">
                  <Fact
                    label="Publisher"
                    value={candidate.source.publishing_organization}
                  />
                  <Fact label="Dataset" value={candidate.source.name} />
                  <Fact
                    label="Record date"
                    value={candidate.source_record_updated_at?.slice(0, 10)}
                  />
                  <Fact
                    label="Dataset date"
                    value={candidate.dataset_updated_at?.slice(0, 10)}
                  />
                  <Fact
                    label="Retrieved"
                    value={candidate.retrieved_at.slice(0, 10)}
                  />
                  <Fact
                    label="License / permission"
                    value={candidate.source.license_name}
                  />
                  <Fact
                    label="Duplicate check"
                    value={candidate.duplicate_classification.replaceAll(
                      "_",
                      " ",
                    )}
                  />
                  <Fact
                    label="Review status"
                    value={candidate.review_status.replaceAll("_", " ")}
                  />
                </dl>
                <a
                  className="mt-5 inline-block rounded-full bg-white px-4 py-2 font-bold"
                  href={candidate.source_url ?? candidate.source.source_url}
                  rel="noreferrer"
                  target="_blank"
                >
                  Open official source ↗
                </a>
              </section>
            </div>
            <section className="glass rounded-3xl p-6">
              <h2 className="text-xl font-bold">Administrator decision</h2>
              <label className="mt-4 grid gap-1 text-sm font-bold">
                Review notes
                <textarea
                  className="min-h-24 rounded-2xl border border-[#bfd0d8] bg-white p-3 font-normal"
                  maxLength={2000}
                  onChange={(event) => setReason(event.target.value)}
                  value={reason}
                />
              </label>
              {error && (
                <p
                  className="mt-3 rounded-xl bg-red-50 p-3 text-red-900"
                  role="alert"
                >
                  {error}
                </p>
              )}
              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  className="rounded-full bg-[#175f75] px-5 py-2.5 font-bold text-white disabled:opacity-50"
                  disabled={
                    busy ||
                    !["ready_for_review", "claimed"].includes(
                      candidate.review_status,
                    )
                  }
                  onClick={approve}
                >
                  Approve as private draft
                </button>
                <button
                  className="rounded-full bg-white px-4 py-2 font-bold disabled:opacity-50"
                  disabled={busy}
                  onClick={() => action("claim")}
                >
                  Claim
                </button>
                <button
                  className="rounded-full bg-white px-4 py-2 font-bold disabled:opacity-50"
                  disabled={busy || !reason}
                  onClick={() => action("defer")}
                >
                  Defer
                </button>
                <button
                  className="rounded-full bg-white px-4 py-2 font-bold disabled:opacity-50"
                  disabled={busy || !reason}
                  onClick={() => action("request-source-review")}
                >
                  Request source review
                </button>
                <button
                  className="rounded-full bg-red-50 px-4 py-2 font-bold text-red-900 disabled:opacity-50"
                  disabled={busy || !reason}
                  onClick={() => action("reject")}
                >
                  Reject
                </button>
              </div>
            </section>
            {candidate.audit_history && candidate.audit_history.length > 0 && (
              <section className="glass-subtle rounded-3xl p-6">
                <h2 className="text-xl font-bold">Review history</h2>
                <ul className="mt-4 grid gap-2">
                  {candidate.audit_history.map((event) => (
                    <li
                      className="rounded-xl bg-white/70 p-3 text-sm"
                      key={`${event.action}-${event.created_at}`}
                    >
                      <strong>{event.action}</strong> · {event.summary}
                      <br />
                      <span className="text-[var(--muted)]">
                        {new Date(event.created_at).toLocaleString()}
                      </span>
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </div>
        )
      }
    </AdminShell>
  );
}

function Fact({
  label,
  value,
  wide = false,
}: {
  label: string;
  value: string | null | undefined;
  wide?: boolean;
}) {
  return (
    <div className={wide ? "sm:col-span-2" : ""}>
      <dt className="text-xs font-bold uppercase text-[var(--muted)]">
        {label}
      </dt>
      <dd className="mt-1 break-words">{value || "Not provided"}</dd>
    </div>
  );
}
