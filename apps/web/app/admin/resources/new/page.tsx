"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { AdminShell } from "@/components/admin/admin-shell";
import { GovernedResource, adminFetch } from "@/lib/admin-api";

export default function NewResourcePage() {
  return <AdminShell>{() => <NewDraft />}</AdminShell>;
}
function NewDraft() {
  const router = useRouter();
  const [error, setError] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const value = (name: string) => String(data.get(name) ?? "");
    try {
      const item = await adminFetch<GovernedResource>("resources", {
        method: "POST",
        body: JSON.stringify({
          content: {
            organization_name: value("organization_name"),
            organization_description: value("organization_description"),
            organization_type: value("organization_type"),
            service_name: value("service_name"),
            description: value("description"),
            eligibility: value("eligibility") || null,
            languages: value("languages")
              .split(",")
              .map((x) => x.trim())
              .filter(Boolean),
            accessibility: value("accessibility") || null,
            emergency_availability: data.get("emergency_availability") === "on",
            source_name: value("source_name"),
            source_url: value("source_url"),
            source_organization: value("source_organization"),
          },
        }),
      });
      router.push(`/admin/resources/${item.id}`);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Draft creation failed",
      );
    }
  }
  return (
    <section className="glass rounded-3xl p-6 sm:p-8">
      <p className="eyebrow">New governed resource</p>
      <h1 className="mt-2 text-3xl font-extrabold">Create a draft</h1>
      {error && (
        <p role="alert" className="mt-4 bg-red-50 p-3">
          {error}
        </p>
      )}
      <form className="mt-6 grid gap-4" onSubmit={submit}>
        {[
          ["Organization name", "organization_name"],
          ["Organization description", "organization_description"],
          ["Organization type", "organization_type"],
          ["Service name", "service_name"],
          ["Service description", "description"],
          ["Eligibility", "eligibility"],
          ["Languages (comma separated)", "languages"],
          ["Accessibility", "accessibility"],
          ["Source name", "source_name"],
          ["Source URL", "source_url"],
          ["Source organization", "source_organization"],
        ].map(([label, name]) => (
          <label className="grid gap-2 font-bold" key={name}>
            {label}
            {name.includes("description") ? (
              <textarea
                className="rounded-2xl border bg-white px-4 py-3"
                name={name}
                required
                rows={4}
              />
            ) : (
              <input
                className="rounded-2xl border bg-white px-4 py-3"
                name={name}
                required={!["eligibility", "accessibility"].includes(name)}
                type={name === "source_url" ? "url" : "text"}
              />
            )}
          </label>
        ))}
        <label>
          <input
            className="mr-2"
            name="emergency_availability"
            type="checkbox"
          />
          Emergency availability
        </label>
        <button className="rounded-2xl bg-[#176d83] px-5 py-3 font-bold text-white">
          Create draft
        </button>
      </form>
    </section>
  );
}
