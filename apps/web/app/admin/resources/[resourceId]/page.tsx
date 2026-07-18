"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AdminShell } from "@/components/admin/admin-shell";
import { ActionDialog } from "@/components/dialogs/action-dialog";
import { GovernedResource, adminFetch } from "@/lib/admin-api";

const actions: Record<
  string,
  { action: string; label: string; reason?: boolean; verify?: boolean }[]
> = {
  draft: [{ action: "submit", label: "Submit for review" }],
  changes_requested: [{ action: "submit", label: "Resubmit" }],
  submitted: [
    { action: "claim", label: "Claim review" },
    { action: "request-changes", label: "Request changes", reason: true },
    { action: "reject", label: "Reject", reason: true },
    { action: "advance", label: "Advance to verification" },
  ],
  pending_verification: [
    { action: "verify", label: "Record verification", verify: true },
    { action: "reject", label: "Reject", reason: true },
  ],
  verified: [{ action: "publish", label: "Publish resource" }],
  published: [
    { action: "reverify", label: "Request re-verification" },
    { action: "archive", label: "Archive", reason: true },
  ],
  needs_reverification: [
    { action: "verify", label: "Complete re-verification", verify: true },
    { action: "archive", label: "Archive", reason: true },
  ],
};

export default function ResourcePage() {
  return <AdminShell>{() => <ResourceDetail />}</AdminShell>;
}
function ResourceDetail() {
  const { resourceId } = useParams<{ resourceId: string }>();
  const [item, setItem] = useState<GovernedResource | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [selected, setSelected] = useState<{
    action: string;
    label: string;
    reason?: boolean;
    verify?: boolean;
  } | null>(null);
  const [reason, setReason] = useState("");
  const [evidence, setEvidence] = useState("");
  const [nextDue, setNextDue] = useState("");
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    void adminFetch<GovernedResource>(`resources/${resourceId}`)
      .then(setItem)
      .catch((e) => setError(e.message));
  }, [resourceId]);
  async function act() {
    if (!item) return;
    if (!selected) return;
    setLoading(true);
    try {
      const updated = await adminFetch<GovernedResource>(
        `resources/${resourceId}/${selected.action}`,
        {
          method: "POST",
          body: JSON.stringify({
            expected_revision: item.revision,
            reason: reason || null,
            evidence: evidence ? [evidence] : [],
            next_due_at: nextDue ? new Date(nextDue).toISOString() : null,
          }),
        },
      );
      setItem(updated);
      setNotice(`Resource moved to ${updated.state.replaceAll("_", " ")}.`);
      setSelected(null);
      setReason("");
      setEvidence("");
      setNextDue("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Action failed");
    } finally {
      setLoading(false);
    }
  }
  if (!item) return <p aria-busy="true">Loading resource…</p>;
  return (
    <div className="grid gap-5">
      <section className="glass rounded-3xl p-6 sm:p-8">
        <p className="eyebrow">
          {item.state.replaceAll("_", " ")} · revision {item.revision}
        </p>
        <h1 className="mt-2 text-3xl font-extrabold">
          {item.content.service_name}
        </h1>
        <p className="mt-1 text-[var(--muted)]">
          {item.content.organization_name}
        </p>
        {error && (
          <p role="alert" className="mt-4 rounded-xl bg-red-50 p-3">
            {error}
          </p>
        )}
        {notice && (
          <p role="status" className="mt-4 rounded-xl bg-emerald-50 p-3">
            {notice}
          </p>
        )}
        <div className="mt-6 flex flex-wrap gap-2">
          {(actions[item.state] ?? []).map((entry) => (
            <button
              className="rounded-full bg-white px-4 py-2 font-bold shadow-sm"
              key={entry.action}
              onClick={() => setSelected(entry)}
            >
              {entry.label}
            </button>
          ))}
          {item.public_service_id && (
            <Link
              className="rounded-full bg-[#176d83] px-4 py-2 font-bold text-white"
              href={`/resources/${item.public_service_id}`}
            >
              View public resource
            </Link>
          )}
        </div>
      </section>
      <ActionDialog
        open={selected !== null}
        title={selected?.label ?? "Resource action"}
        description="Review this governed action before continuing. The server validates state, permissions, and the expected revision."
        submitLabel={selected?.label ?? "Continue"}
        destructive={
          selected?.action === "archive" || selected?.action === "reject"
        }
        loading={loading}
        error={error}
        onClose={() => setSelected(null)}
        onSubmit={act}
      >
        {selected?.reason && (
          <label className="grid gap-2 font-bold">
            Required reason
            <textarea
              autoFocus
              required
              minLength={3}
              maxLength={2000}
              rows={4}
              className="rounded-xl border bg-white p-3 font-normal"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          </label>
        )}
        {selected?.verify && (
          <>
            <label className="grid gap-2 font-bold">
              Evidence URL
              <input
                autoFocus
                required
                type="url"
                className="rounded-xl border bg-white p-3 font-normal"
                value={evidence}
                onChange={(e) => setEvidence(e.target.value)}
              />
            </label>
            <label className="grid gap-2 font-bold">
              Next verification date
              <input
                required
                type="date"
                className="rounded-xl border bg-white p-3 font-normal"
                value={nextDue}
                onChange={(e) => setNextDue(e.target.value)}
              />
            </label>
          </>
        )}
        {(selected?.action === "archive" || selected?.action === "reject") && (
          <label className="flex items-start gap-3">
            <input type="checkbox" required />
            <span>
              I understand this action removes or rejects this resource from its
              current workflow.
            </span>
          </label>
        )}
      </ActionDialog>
      <section className="glass-subtle rounded-3xl p-6">
        <h2 className="text-xl font-bold">Current revision</h2>
        <dl className="mt-4 grid gap-3">
          <Field label="Description" value={item.content.description} />
          <Field
            label="Eligibility"
            value={item.content.eligibility ?? "Not specified"}
          />
          <Field
            label="Languages"
            value={item.content.languages.join(", ") || "Not specified"}
          />
          <Field
            label="Accessibility"
            value={item.content.accessibility ?? "Not specified"}
          />
          <Field
            label="Source"
            value={`${item.content.source_name} — ${item.content.source_url}`}
          />
        </dl>
      </section>
    </div>
  );
}
function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-white/75 p-4">
      <dt className="font-bold">{label}</dt>
      <dd className="mt-1 text-[var(--muted)]">{value}</dd>
    </div>
  );
}
