"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AdminShell } from "@/components/admin/admin-shell";
import { ProposedRevisionEditor } from "@/components/admin/proposed-revision-editor";
import { ActionDialog } from "@/components/dialogs/action-dialog";
import { adminFetch, ReverificationTask } from "@/lib/admin-api";
function defaultNextDueAt() {
  const due = new Date();
  due.setUTCDate(due.getUTCDate() + 90);
  return due.toISOString();
}
export default function Page() {
  return <AdminShell>{() => <Detail />}</AdminShell>;
}
function Detail() {
  const { taskId } = useParams<{ taskId: string }>();
  const [item, setItem] = useState<ReverificationTask | null>(null);
  const [evidence, setEvidence] = useState("");
  const [sources, setSources] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    void adminFetch<ReverificationTask>(`reverification/${taskId}`)
      .then((x) => {
        setItem(x);
        setEvidence(x.evidence_summary ?? "");
        setSources((x.source_references ?? []).join("\n"));
      })
      .catch((e) => setError(e.message));
  }, [taskId]);
  async function act(action: string) {
    if (!item) return;
    setLoading(true);
    try {
      const updated = await adminFetch<ReverificationTask>(
        `reverification/${item.id}/${action}`,
        {
          method: "POST",
          body: JSON.stringify({
            expected_version: item.version,
            evidence_summary: evidence || null,
            source_references: sources
              .split("\n")
              .map((x) => x.trim())
              .filter(Boolean),
            next_due_at: defaultNextDueAt(),
          }),
        },
      );
      setItem(updated);
      setNotice(`${action.replaceAll("-", " ")} completed.`);
      setSelectedAction(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setLoading(false);
    }
  }
  if (!item) return <p aria-busy="true">Loading task…</p>;
  return (
    <div className="grid gap-5">
      <section className="glass rounded-3xl p-6">
        <Link className="underline" href="/admin/reverification">
          ← Re-verification queue
        </Link>
        <p className="eyebrow mt-5">
          {item.status.replaceAll("_", " ")} · version {item.version}
        </p>
        <h1 className="mt-2 text-3xl font-extrabold">
          {item.reason.replaceAll("_", " ")}
        </h1>
        <p className="mt-3">
          Triggered by {item.trigger_source.replaceAll("_", " ")}; due{" "}
          {new Date(item.due_at).toLocaleDateString()}.
        </p>
        {notice && (
          <p role="status" className="mt-4 rounded-xl bg-emerald-50 p-3">
            {notice}
          </p>
        )}
        {error && (
          <p role="alert" className="mt-4 rounded-xl bg-red-50 p-3">
            {error}
          </p>
        )}
      </section>
      {item.resource_id && (
        <ProposedRevisionEditor task={item} onTaskChange={setItem} />
      )}
      <section className="glass-subtle rounded-3xl p-6">
        <h2 className="text-xl font-bold">Evidence and outcome</h2>
        <label className="mt-4 grid gap-2 font-bold">
          Evidence summary
          <textarea
            rows={5}
            maxLength={5000}
            className="rounded-xl border bg-white p-3"
            value={evidence}
            onChange={(e) => setEvidence(e.target.value)}
          />
        </label>
        <label className="mt-4 grid gap-2 font-bold">
          Source references{" "}
          <span className="font-normal">(one URL per line)</span>
          <textarea
            rows={4}
            className="rounded-xl border bg-white p-3"
            value={sources}
            onChange={(e) => setSources(e.target.value)}
          />
        </label>
        <div className="mt-5 flex flex-wrap gap-2">
          {[
            "claim",
            "release",
            "start",
            "update-evidence",
            "confirmed-unchanged",
            "could-not-confirm",
            "provider-unavailable",
            "source-unavailable",
            "resource-closed",
            "archive",
            "escalate",
            "cancel-duplicate",
          ].map((action) => (
            <button
              className="rounded-full bg-white px-4 py-2 font-bold shadow-sm"
              onClick={() => setSelectedAction(action)}
              key={action}
            >
              {action.replaceAll("-", " ")}
            </button>
          ))}
        </div>
      </section>
      <ActionDialog
        open={selectedAction !== null}
        title={`${selectedAction?.replaceAll("-", " ") ?? "Task action"}?`}
        description="This version-checked action is recorded in the audit history. Evidence is required for verification outcomes."
        submitLabel={selectedAction?.replaceAll("-", " ") ?? "Continue"}
        destructive={
          selectedAction === "archive" ||
          selectedAction === "resource-closed" ||
          selectedAction === "cancel-duplicate"
        }
        loading={loading}
        error={error}
        onClose={() => setSelectedAction(null)}
        onSubmit={() => {
          if (selectedAction) return act(selectedAction);
        }}
      >
        {!["claim", "release", "start", "cancel-duplicate"].includes(
          selectedAction ?? "",
        ) && (
          <label className="grid gap-2 font-bold">
            Evidence summary
            <textarea
              required
              minLength={10}
              maxLength={5000}
              rows={4}
              className="rounded-xl border bg-white p-3 font-normal"
              value={evidence}
              onChange={(e) => setEvidence(e.target.value)}
            />
          </label>
        )}
        {(selectedAction === "confirmed-unchanged" ||
          selectedAction === "update-evidence") && (
          <label className="grid gap-2 font-bold">
            Source references <span className="font-normal">one per line</span>
            <textarea
              rows={3}
              className="rounded-xl border bg-white p-3 font-normal"
              value={sources}
              onChange={(e) => setSources(e.target.value)}
            />
          </label>
        )}
        {(selectedAction === "archive" ||
          selectedAction === "resource-closed" ||
          selectedAction === "cancel-duplicate") && (
          <label className="flex items-start gap-3">
            <input type="checkbox" required />
            <span>
              I understand this action changes resource availability or closes
              this task.
            </span>
          </label>
        )}
      </ActionDialog>
    </div>
  );
}
