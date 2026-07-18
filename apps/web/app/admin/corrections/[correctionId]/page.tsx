"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AdminShell } from "@/components/admin/admin-shell";
import { adminFetch, Correction } from "@/lib/admin-api";

export default function CorrectionPage() {
  return <AdminShell>{() => <Detail />}</AdminShell>;
}
function Detail() {
  const { correctionId } = useParams<{ correctionId: string }>();
  const [item, setItem] = useState<Correction | null>(null);
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  useEffect(() => {
    void adminFetch<Correction>(`corrections/${correctionId}`)
      .then(setItem)
      .catch((e) => setError(e.message));
  }, [correctionId]);
  async function act(action: string) {
    if (!item) return;
    setError("");
    try {
      const updated = await adminFetch<Correction>(
        `corrections/${item.id}/${action}`,
        {
          method: "POST",
          body: JSON.stringify({
            expected_version: item.version,
            reason: reason || null,
          }),
        },
      );
      setItem(updated);
      setNotice(`${action.replaceAll("-", " ")} completed.`);
      setReason("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
    }
  }
  if (!item) return <p aria-busy="true">Loading correction…</p>;
  return (
    <div className="grid gap-5">
      <section className="glass rounded-3xl p-6 sm:p-8">
        <Link className="underline" href="/admin/corrections">
          ← Correction queue
        </Link>
        <p className="eyebrow mt-5">
          {item.status.replaceAll("_", " ")} · version {item.version}
        </p>
        <h1 className="mt-2 text-3xl font-extrabold">
          {item.category.replaceAll("_", " ")}
        </h1>
        <p className="mt-5 whitespace-pre-wrap rounded-2xl bg-white/75 p-4">
          {item.description}
        </p>
        {item.reporter_name && (
          <p className="mt-4">
            <strong>Reporter:</strong> {item.reporter_name}
            {item.reporter_email && (
              <>
                {" "}
                ·{" "}
                <a className="underline" href={`mailto:${item.reporter_email}`}>
                  {item.reporter_email}
                </a>
              </>
            )}
          </p>
        )}
        {item.task_id && (
          <Link
            className="mt-4 block font-bold underline"
            href={`/admin/reverification/${item.task_id}`}
          >
            Open related re-verification task
          </Link>
        )}
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
      <section className="glass-subtle rounded-3xl p-6">
        <h2 className="text-xl font-bold">Workflow actions</h2>
        <label className="mt-4 grid gap-2 font-bold">
          Reason or resolution note
          <textarea
            className="rounded-xl border bg-white p-3"
            rows={4}
            maxLength={2000}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
        </label>
        <div className="mt-4 flex flex-wrap gap-2">
          {[
            "claim",
            "release",
            "triage",
            "escalate",
            "resolve",
            "dismiss",
            "abuse",
            "reopen",
          ].map((action) => (
            <button
              className="rounded-full bg-white px-4 py-2 font-bold shadow-sm"
              onClick={() => void act(action)}
              key={action}
            >
              {action.replaceAll("-", " ")}
            </button>
          ))}
        </div>
        <p className="mt-4 text-sm text-[var(--muted)]">
          Actions are version-checked and audited. Resolution, dismissal, and
          abuse classification require a reason.
        </p>
      </section>
    </div>
  );
}
