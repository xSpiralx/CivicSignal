"use client";
import { useEffect, useMemo, useState } from "react";
import { ActionDialog } from "@/components/dialogs/action-dialog";
import {
  adminFetch,
  DraftContent,
  Proposal,
  ReverificationTask,
} from "@/lib/admin-api";

const labels: Record<string, string> = {
  service_name: "Resource name",
  organization_name: "Organization",
  organization_description: "Organization description",
  organization_type: "Organization type",
  description: "Description",
  categories: "Categories",
  contact_phone: "Phone",
  contact_email: "Email",
  website: "Website",
  location_name: "Location",
  city: "City",
  region: "State or region",
  postal_code: "Postal code",
  service_area: "Service area",
  remote_service_available: "Remote service",
  emergency_availability: "Emergency availability",
  hours: "Hours",
  eligibility: "Eligibility",
  required_documents: "Required documents",
  cost_information: "Cost",
  languages: "Languages",
  accessibility: "Accessibility",
  transportation: "Transportation",
  application_instructions: "Application instructions",
  source_name: "Source title",
  source_organization: "Source organization",
  source_url: "Source URL",
  source_type: "Source type",
  source_retrieved_at: "Retrieval/contact date",
  source_notes: "Source notes",
  source_public: "Public source",
  source_supports_changed_fields: "Supports changed fields",
};

function display(value: unknown) {
  if (value == null || value === "" || (Array.isArray(value) && !value.length))
    return "Not specified";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}
function Input({
  label,
  value,
  onChange,
  area = false,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  area?: boolean;
  type?: string;
}) {
  return (
    <label className="grid gap-2 font-bold">
      {label}
      {area ? (
        <textarea
          rows={4}
          className="rounded-xl border bg-white p-3 font-normal"
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
      ) : (
        <input
          type={type}
          className="rounded-xl border bg-white p-3 font-normal"
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
      )}
    </label>
  );
}

export function ProposedRevisionEditor({
  task,
  onTaskChange,
}: {
  task: ReverificationTask;
  onTaskChange: (task: ReverificationTask) => void;
}) {
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [content, setContent] = useState<DraftContent | null>(null);
  const [saved, setSaved] = useState("");
  const [error, setError] = useState("");
  const [conflict, setConflict] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [dialog, setDialog] = useState<"discard" | "publish" | null>(null);
  const [evidence, setEvidence] = useState("");
  const [loading, setLoading] = useState(false);
  const load = () =>
    adminFetch<Proposal>(`reverification/${task.id}/proposal`)
      .then((p) => {
        setProposal(p);
        setContent(p.proposed_content);
        setConflict(false);
        setError("");
        setDirty(false);
      })
      .catch((e) => setError(e.message));
  useEffect(() => {
    void adminFetch<Proposal>(`reverification/${task.id}/proposal`)
      .then((p) => {
        setProposal(p);
        setContent(p.proposed_content);
        setConflict(false);
        setError("");
        setDirty(false);
      })
      .catch((e) => setError(e.message));
  }, [task.id]);
  useEffect(() => {
    const warn = (e: BeforeUnloadEvent) => {
      if (dirty) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);
  const changed = useMemo(() => proposal?.changed_fields ?? [], [proposal]);
  function set<K extends keyof DraftContent>(key: K, value: DraftContent[K]) {
    setContent((c) => (c ? { ...c, [key]: value } : c));
    setDirty(true);
    setSaved("");
  }
  async function save() {
    if (!proposal || !content) return;
    setLoading(true);
    setError("");
    try {
      const next = await adminFetch<Proposal>(
        `reverification/${task.id}/proposal`,
        {
          method: "POST",
          body: JSON.stringify({
            expected_task_version: proposal.task_version,
            expected_revision: proposal.proposed_revision,
            content,
          }),
        },
      );
      setProposal(next);
      setContent(next.proposed_content);
      setDirty(false);
      setSaved(`Saved as revision ${next.proposed_revision}.`);
      onTaskChange({ ...task, version: next.task_version });
    } catch (e) {
      const err = e as Error & { status?: number };
      setError(
        err.status === 409
          ? "Another user changed this task. Your unsaved text is preserved; reload the newest revision before saving again."
          : err.message,
      );
      setConflict(err.status === 409);
    } finally {
      setLoading(false);
    }
  }
  async function discard() {
    if (!proposal) return;
    setLoading(true);
    try {
      const next = await adminFetch<Proposal>(
        `reverification/${task.id}/proposal/discard`,
        {
          method: "POST",
          body: JSON.stringify({ expected_version: proposal.task_version }),
        },
      );
      setProposal(next);
      setContent(next.proposed_content);
      setDirty(false);
      setDialog(null);
      onTaskChange({ ...task, version: next.task_version });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Discard failed");
    } finally {
      setLoading(false);
    }
  }
  async function publish() {
    if (!proposal) return;
    setLoading(true);
    try {
      const completed = await adminFetch<ReverificationTask>(
        `reverification/${task.id}/updated-confirmed`,
        {
          method: "POST",
          body: JSON.stringify({
            expected_version: proposal.task_version,
            expected_revision: proposal.proposed_revision,
            evidence_summary: evidence,
            source_references: [content?.source_url].filter(Boolean),
            next_due_at: new Date(
              new Date().setUTCDate(new Date().getUTCDate() + 90),
            ).toISOString(),
          }),
        },
      );
      onTaskChange(completed);
      setDialog(null);
      setSaved("The proposed revision was verified and published.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Publication failed");
    } finally {
      setLoading(false);
    }
  }
  if (!proposal || !content)
    return (
      <section className="glass-subtle rounded-3xl p-6" aria-busy="true">
        <h2 className="text-xl font-bold">Proposed revision</h2>
        <p>{error || "Loading published revision…"}</p>
      </section>
    );
  return (
    <section className="glass-subtle rounded-3xl p-6 sm:p-8">
      <div className="flex flex-wrap justify-between gap-3">
        <div>
          <p className="eyebrow">
            Published {proposal.published_revision} · proposed{" "}
            {proposal.proposed_revision}
          </p>
          <h2 className="mt-2 text-2xl font-extrabold">
            Proposed revision editor
          </h2>
        </div>
        <span
          className={`h-fit rounded-full px-3 py-1 text-sm font-bold ${proposal.ready ? "bg-emerald-100" : "bg-amber-100"}`}
        >
          {proposal.ready ? "Ready" : "Not ready"}
        </span>
      </div>
      {error && (
        <div role="alert" className="mt-4 rounded-xl bg-red-50 p-3">
          {error}
          {conflict && (
            <button
              className="ml-2 font-bold underline"
              onClick={() => void load()}
            >
              Reload newest revision
            </button>
          )}
        </div>
      )}
      {saved && (
        <p role="status" className="mt-4 rounded-xl bg-emerald-50 p-3">
          {saved}
        </p>
      )}
      <div className="mt-6 grid gap-5 sm:grid-cols-2">
        <Input
          label="Public resource name"
          value={content.service_name}
          onChange={(v) => set("service_name", v)}
        />
        <Input
          label="Organization"
          value={content.organization_name}
          onChange={(v) => set("organization_name", v)}
        />
        <Input
          label="Organization type"
          value={content.organization_type}
          onChange={(v) => set("organization_type", v)}
        />
        <div className="sm:col-span-2">
          <Input
            area
            label="Organization description"
            value={content.organization_description}
            onChange={(v) => set("organization_description", v)}
          />
        </div>
        <div className="sm:col-span-2">
          <Input
            area
            label="Description"
            value={content.description}
            onChange={(v) => set("description", v)}
          />
        </div>
        <Input
          label="Categories (comma separated)"
          value={content.categories.join(", ")}
          onChange={(v) =>
            set(
              "categories",
              v
                .split(",")
                .map((x) => x.trim())
                .filter(Boolean),
            )
          }
        />
        <Input
          label="Languages (comma separated)"
          value={content.languages.join(", ")}
          onChange={(v) =>
            set(
              "languages",
              v
                .split(",")
                .map((x) => x.trim())
                .filter(Boolean),
            )
          }
        />
        <Input
          label="Phone"
          value={content.contact_phone ?? ""}
          onChange={(v) => set("contact_phone", v || null)}
        />
        <Input
          type="email"
          label="Email"
          value={content.contact_email ?? ""}
          onChange={(v) => set("contact_email", v || null)}
        />
        <Input
          type="url"
          label="Website"
          value={content.website ?? ""}
          onChange={(v) => set("website", v || null)}
        />
        <Input
          label="Hours"
          value={content.hours ?? ""}
          onChange={(v) => set("hours", v || null)}
        />
        <Input
          label="Location name"
          value={content.location_name ?? ""}
          onChange={(v) => set("location_name", v || null)}
        />
        <Input
          label="Service area"
          value={content.service_area ?? ""}
          onChange={(v) => set("service_area", v || null)}
        />
        <Input
          label="City"
          value={content.city ?? ""}
          onChange={(v) => set("city", v || null)}
        />
        <Input
          label="State or region"
          value={content.region ?? ""}
          onChange={(v) => set("region", v || null)}
        />
        <Input
          label="Postal code"
          value={content.postal_code ?? ""}
          onChange={(v) => set("postal_code", v || null)}
        />
        <label className="flex items-center gap-3 font-bold">
          <input
            type="checkbox"
            checked={content.remote_service_available}
            onChange={(e) => set("remote_service_available", e.target.checked)}
          />
          Remote service available
        </label>
        <label className="flex items-center gap-3 font-bold">
          <input
            type="checkbox"
            checked={content.emergency_availability}
            onChange={(e) => set("emergency_availability", e.target.checked)}
          />
          Emergency availability
        </label>
        <div className="sm:col-span-2">
          <Input
            area
            label="Eligibility"
            value={content.eligibility ?? ""}
            onChange={(v) => set("eligibility", v || null)}
          />
        </div>
        <Input
          area
          label="Required documents"
          value={content.required_documents ?? ""}
          onChange={(v) => set("required_documents", v || null)}
        />
        <Input
          area
          label="Cost information"
          value={content.cost_information ?? ""}
          onChange={(v) => set("cost_information", v || null)}
        />
        <Input
          area
          label="Accessibility"
          value={content.accessibility ?? ""}
          onChange={(v) => set("accessibility", v || null)}
        />
        <Input
          area
          label="Transportation"
          value={content.transportation ?? ""}
          onChange={(v) => set("transportation", v || null)}
        />
        <div className="sm:col-span-2">
          <Input
            area
            label="Application instructions"
            value={content.application_instructions ?? ""}
            onChange={(v) => set("application_instructions", v || null)}
          />
        </div>
      </div>
      <fieldset className="mt-7 grid gap-5 rounded-2xl bg-white/60 p-5 sm:grid-cols-2">
        <legend className="px-2 text-lg font-bold">Source provenance</legend>
        <Input
          label="Source title"
          value={content.source_name}
          onChange={(v) => set("source_name", v)}
        />
        <Input
          label="Source organization"
          value={content.source_organization}
          onChange={(v) => set("source_organization", v)}
        />
        <Input
          type="url"
          label="Source URL"
          value={content.source_url}
          onChange={(v) => set("source_url", v)}
        />
        <Input
          label="Source type"
          value={content.source_type}
          onChange={(v) => set("source_type", v)}
        />
        <Input
          type="date"
          label="Retrieval or contact date"
          value={content.source_retrieved_at?.slice(0, 10) ?? ""}
          onChange={(v) =>
            set(
              "source_retrieved_at",
              v ? new Date(`${v}T00:00:00Z`).toISOString() : null,
            )
          }
        />
        <Input
          area
          label="Source notes"
          value={content.source_notes ?? ""}
          onChange={(v) => set("source_notes", v || null)}
        />
        <label className="flex items-center gap-3 font-bold">
          <input
            type="checkbox"
            checked={content.source_public}
            onChange={(e) => set("source_public", e.target.checked)}
          />{" "}
          Public source
        </label>
        <label className="flex items-center gap-3 font-bold">
          <input
            type="checkbox"
            checked={content.source_supports_changed_fields}
            onChange={(e) =>
              set("source_supports_changed_fields", e.target.checked)
            }
          />{" "}
          Supports the changed fields
        </label>
      </fieldset>
      <section className="mt-7" aria-labelledby="readiness">
        <h3 id="readiness" className="text-xl font-bold">
          Readiness summary
        </h3>
        {proposal.blocking_errors.length > 0 && (
          <ul className="mt-3 list-disc pl-6">
            {proposal.blocking_errors.map((x) => (
              <li key={x}>{x}</li>
            ))}
          </ul>
        )}
        {proposal.warnings.length > 0 && (
          <ul className="mt-3 list-disc pl-6 text-[var(--muted)]">
            {proposal.warnings.map((x) => (
              <li key={x}>{x}</li>
            ))}
          </ul>
        )}
      </section>
      <section className="mt-7" aria-labelledby="comparison">
        <h3 id="comparison" className="text-xl font-bold">
          Published versus proposed
        </h3>
        {changed.length === 0 ? (
          <p className="mt-2">No saved differences.</p>
        ) : (
          <div className="mt-4 grid gap-4">
            {changed.map((key) => (
              <article
                className="overflow-hidden rounded-2xl bg-white/70"
                key={key}
              >
                <h4 className="px-4 pt-4 font-bold">
                  {labels[key] ?? key.replaceAll("_", " ")}
                </h4>
                <div className="grid gap-3 p-4 sm:grid-cols-2">
                  <div>
                    <span className="text-sm font-bold">Published</span>
                    <p className="mt-1 whitespace-pre-wrap break-words">
                      {display(
                        proposal.published_content[key as keyof DraftContent],
                      )}
                    </p>
                  </div>
                  <div>
                    <span className="text-sm font-bold">Proposed</span>
                    <p className="mt-1 whitespace-pre-wrap break-words">
                      {display(
                        proposal.proposed_content[key as keyof DraftContent],
                      )}
                    </p>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
      <div className="mt-7 flex flex-wrap gap-3">
        <button
          disabled={!dirty || loading}
          onClick={() => void save()}
          className="rounded-full bg-[#176d83] px-5 py-3 font-bold text-white disabled:opacity-50"
        >
          {loading ? "Saving…" : "Save proposed revision"}
        </button>
        <button
          onClick={() => setDialog("discard")}
          className="rounded-full bg-white px-5 py-3 font-bold"
        >
          Discard proposed changes
        </button>
        <button
          disabled={!proposal.ready || dirty || task.status === "completed"}
          onClick={() => setDialog("publish")}
          className="rounded-full bg-emerald-700 px-5 py-3 font-bold text-white disabled:opacity-50"
        >
          Review and publish
        </button>
      </div>
      <ActionDialog
        open={dialog === "discard"}
        title="Discard proposed changes?"
        description="The working pointer will return to the published revision. Superseded immutable revisions remain in history."
        submitLabel="Discard proposed changes"
        destructive
        loading={loading}
        error={error}
        onClose={() => setDialog(null)}
        onSubmit={discard}
      >
        <label className="flex items-start gap-3">
          <input type="checkbox" required />{" "}
          <span>
            I understand the unsaved working proposal will be discarded.
          </span>
        </label>
      </ActionDialog>
      <ActionDialog
        open={dialog === "publish"}
        title="Verify and publish this revision?"
        description="This creates a new public verification, advances the published pointer, completes the task, and resolves related corrections in one transaction."
        submitLabel="Publish verified revision"
        loading={loading}
        error={error}
        onClose={() => setDialog(null)}
        onSubmit={publish}
      >
        <label className="grid gap-2 font-bold">
          Verification evidence
          <textarea
            autoFocus
            required
            minLength={10}
            maxLength={5000}
            rows={5}
            className="rounded-xl border bg-white p-3 font-normal"
            value={evidence}
            onChange={(e) => setEvidence(e.target.value)}
          />
        </label>
      </ActionDialog>
    </section>
  );
}
