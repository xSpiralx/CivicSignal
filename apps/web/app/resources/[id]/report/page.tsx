"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useRef, useState } from "react";
import { formatChecked, ServiceDetail } from "@/lib/resources";

const categories = [
  ["incorrect_phone", "Incorrect phone number"],
  ["incorrect_address", "Incorrect address"],
  ["incorrect_hours", "Incorrect hours"],
  ["broken_website", "Broken website"],
  ["resource_closed", "Resource appears closed"],
  ["service_unavailable", "Service appears unavailable"],
  ["eligibility_changed", "Eligibility changed"],
  ["accessibility_incorrect", "Accessibility information incorrect"],
  ["language_incorrect", "Language information incorrect"],
  ["other", "Other"],
];

export default function CorrectionPage() {
  const { id } = useParams<{ id: string }>();
  const started = useRef(new Date().toISOString());
  const [status, setStatus] = useState<"idle" | "submitting" | "success">(
    "idle",
  );
  const [error, setError] = useState("");
  const [resource, setResource] = useState<ServiceDetail | null>(null);
  useEffect(() => {
    void fetch(`/api/resources/services/${id}`, { cache: "no-store" })
      .then((response) => {
        if (!response.ok) throw new Error("Resource unavailable");
        return response.json() as Promise<ServiceDetail>;
      })
      .then(setResource)
      .catch(() => setError("The resource could not be loaded."));
  }, [id]);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setStatus("submitting");
    const form = event.currentTarget;
    const data = new FormData(form);
    const response = await fetch(`/api/resources/services/${id}/corrections`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        category: data.get("category"),
        description: data.get("description"),
        reporter_name: data.get("reporter_name") || null,
        reporter_email: data.get("reporter_email") || null,
        website: data.get("website"),
        form_started_at: started.current,
      }),
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      setError(
        response.status === 429
          ? "Too many reports were submitted. Please try again later."
          : (body?.error?.message ??
              "Your report could not be submitted safely."),
      );
      setStatus("idle");
      return;
    }
    form.reset();
    setStatus("success");
  }
  return (
    <main id="main-content" className="mx-auto max-w-3xl px-5 py-10 sm:px-8">
      <Link className="font-semibold underline" href={`/resources/${id}`}>
        ← Return to resource
      </Link>
      <section className="glass mt-6 rounded-[2rem] p-6 sm:p-9">
        <p className="eyebrow">Community correction</p>
        <h1 className="mt-2 text-4xl font-extrabold">
          Report incorrect information
        </h1>
        {resource ? (
          <div className="mt-5 rounded-2xl bg-white/70 p-4">
            <strong>{resource.name}</strong>
            <p className="text-sm text-[var(--muted)]">
              {resource.organization.public_name} · last checked{" "}
              {formatChecked(resource.verification.last_checked_at)}
            </p>
          </div>
        ) : (
          <p className="mt-4" aria-busy="true">
            Loading resource details…
          </p>
        )}
        <p className="mt-4">
          Reports are reviewed before changes are made. Submitting this form
          does not immediately alter the listing.
        </p>
        <p className="mt-3 text-sm text-[var(--muted)]">
          Are you an organization representative? You may use this same form to
          request an update and identify your role in the description. A claim
          of representation is never accepted automatically; an administrator
          must verify it before any ownership or publication decision.
        </p>
        <div className="mt-5 rounded-2xl bg-amber-50 p-4">
          <strong>Protect your privacy.</strong> Do not include medical or legal
          records, immigration or abuse narratives, crisis details, passwords,
          Social Security numbers, or government identifiers.
        </div>
        {status === "success" ? (
          <div className="mt-6 rounded-2xl bg-emerald-50 p-5" role="status">
            <h2 className="font-bold">Report received</h2>
            <p>
              Thank you. The report is queued for review and public information
              has not changed.
            </p>
            <Link
              className="mt-3 inline-block underline"
              href={`/resources/${id}`}
            >
              Return to the resource
            </Link>
          </div>
        ) : (
          <form className="mt-7 grid gap-5" onSubmit={submit}>
            <label className="grid gap-2 font-bold">
              What needs attention?
              <select
                required
                name="category"
                className="rounded-xl border bg-white p-3"
              >
                <option value="">Choose a category</option>
                {categories.map(([value, label]) => (
                  <option value={value} key={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label className="grid gap-2 font-bold">
              What appears incorrect?
              <textarea
                required
                minLength={10}
                maxLength={4000}
                rows={7}
                name="description"
                className="rounded-xl border bg-white p-3"
                aria-describedby="description-help"
              />
              <span
                id="description-help"
                className="text-sm font-normal text-[var(--muted)]"
              >
                10–4,000 characters. Include only information needed to verify
                the listing.
              </span>
            </label>
            <div className="grid gap-5 sm:grid-cols-2">
              <label className="grid gap-2 font-bold">
                Name <span className="font-normal">(optional)</span>
                <input
                  maxLength={120}
                  name="reporter_name"
                  className="rounded-xl border bg-white p-3"
                />
              </label>
              <label className="grid gap-2 font-bold">
                Email <span className="font-normal">(optional)</span>
                <input
                  type="email"
                  maxLength={320}
                  name="reporter_email"
                  className="rounded-xl border bg-white p-3"
                />
              </label>
            </div>
            <label className="hidden" aria-hidden="true">
              Website
              <input tabIndex={-1} autoComplete="off" name="website" />
            </label>
            {error && (
              <p className="rounded-xl bg-red-50 p-3" role="alert">
                {error}
              </p>
            )}
            <div className="flex flex-wrap gap-3">
              <button
                disabled={status === "submitting"}
                className="rounded-full bg-[#176d83] px-5 py-3 font-bold text-white disabled:opacity-60"
              >
                {status === "submitting" ? "Submitting…" : "Submit report"}
              </button>
              <Link
                className="rounded-full bg-white px-5 py-3 font-bold"
                href={`/resources/${id}`}
              >
                Cancel
              </Link>
            </div>
          </form>
        )}
      </section>
    </main>
  );
}
