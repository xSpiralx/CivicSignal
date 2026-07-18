import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { SafetyNotice } from "@/components/safety-notice";
import { formatChecked, type ServiceDetail } from "@/lib/resources";
import { internalApiBase } from "@/lib/server-api";

async function getResource(id: string): Promise<ServiceDetail | null> {
  const api = internalApiBase();
  const response = await fetch(
    `${api}/api/v1/services/${encodeURIComponent(id)}`,
    { cache: "no-store" },
  );
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("Resource service unavailable");
  return (await response.json()) as ServiceDetail;
}
export const metadata: Metadata = { title: "Resource details | CivicSignal" };
export default async function ResourceDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resource = await getResource((await params).id);
  if (!resource) notFound();
  const details = [
    ["Eligibility", resource.eligibility],
    ["Required documents", resource.required_documents],
    ["Cost", resource.cost_information],
    ["Application instructions", resource.application_instructions],
    ["Appointments", resource.appointment_requirements],
    ["Accessibility", resource.accessibility],
  ];
  return (
    <main
      id="main-content"
      className="mx-auto max-w-5xl px-5 py-10 sm:px-8 sm:py-14"
    >
      <Link
        className="font-semibold text-[var(--teal-dark)] underline"
        href="/resources"
      >
        ← Back to search
      </Link>
      <div className="mt-5">
        <SafetyNotice />
      </div>
      <article className="glass mt-8 rounded-[2.2rem] p-6 sm:p-10">
        <p className="font-semibold text-[var(--teal-dark)]">
          {resource.categories.map((item) => item.name).join(" · ")}
        </p>
        <h1 className="text-balance mt-2 text-4xl font-extrabold tracking-tight sm:text-5xl">
          {resource.name}
        </h1>
        <p className="text-lg text-[var(--muted)]">
          {resource.organization.public_name}
        </p>
        <p className="mt-5">{resource.description}</p>
        <section
          aria-labelledby="verification"
          className="mt-7 rounded-[1.4rem] border border-white/90 bg-emerald-50/65 p-5"
        >
          <h2 id="verification" className="font-bold">
            {resource.verification.may_be_stale
              ? "Information needs re-verification"
              : "Source-verified listing"}
          </h2>
          <p>
            Last checked {formatChecked(resource.verification.last_checked_at)}.
            Verification does not guarantee current availability.
          </p>
          <p className="mt-2 font-semibold">
            Freshness: {resource.verification.freshness.replaceAll("_", " ")}.
            {resource.verification.next_due_at &&
              ` Next review due ${formatChecked(resource.verification.next_due_at)}.`}
          </p>
          {resource.verification.freshness !== "current" && (
            <p className="mt-2">
              Information may have changed. Confirm availability directly with
              the provider.
            </p>
          )}
        </section>
        <section aria-labelledby="details" className="mt-8">
          <h2 id="details" className="text-2xl font-bold">
            Service details
          </h2>
          <dl className="mt-4 grid gap-4 sm:grid-cols-2">
            {details
              .filter(([, value]) => value)
              .map(([label, value]) => (
                <div key={label}>
                  <dt className="font-bold">{label}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            <div>
              <dt className="font-bold">Languages</dt>
              <dd>{resource.languages.join(", ") || "Not specified"}</dd>
            </div>
          </dl>
        </section>
        <section aria-labelledby="contact" className="mt-8">
          <h2 id="contact" className="text-2xl font-bold">
            Contact
          </h2>
          <ul className="mt-3 space-y-2">
            {resource.contacts.map((item) => (
              <li key={`${item.channel_type}-${item.value}`}>
                <strong>{item.label}:</strong> {item.value}
              </li>
            ))}
          </ul>
        </section>
        {resource.locations.map((location) => (
          <section
            aria-labelledby={`location-${location.display_name}`}
            key={location.display_name}
            className="mt-8"
          >
            <h2
              id={`location-${location.display_name}`}
              className="text-2xl font-bold"
            >
              {location.display_name}
            </h2>
            <p>
              {[
                location.address_line_1,
                location.address_line_2,
                location.city,
                location.region,
                location.postal_code,
              ]
                .filter(Boolean)
                .join(", ")}
            </p>
            {location.hours && (
              <p>
                <strong>Hours:</strong> {location.hours}
              </p>
            )}
            {location.transportation && (
              <p>
                <strong>Transportation:</strong> {location.transportation}
              </p>
            )}
          </section>
        ))}
        <section aria-labelledby="sources" className="mt-8">
          <h2 id="sources" className="text-2xl font-bold">
            Sources
          </h2>
          <ul className="mt-3 space-y-2">
            {resource.sources.map((source) => (
              <li key={source.url}>
                <a
                  className="text-[var(--teal-dark)] underline"
                  href={source.url}
                  rel="noopener noreferrer"
                >
                  {source.name}
                </a>{" "}
                — {source.organization}; checked{" "}
                {formatChecked(source.last_checked_at)}
              </li>
            ))}
          </ul>
        </section>
        <section
          className="mt-8 rounded-3xl bg-white/65 p-5"
          aria-labelledby="correction"
        >
          <h2 id="correction" className="text-xl font-bold">
            Is something incorrect?
          </h2>
          <p className="mt-2 text-[var(--muted)]">
            Send a correction for review. Reports never change public
            information automatically.
          </p>
          <Link
            className="mt-4 inline-flex rounded-full bg-[#176d83] px-4 py-2 font-bold text-white"
            href={`/resources/${resource.id}/report`}
          >
            Report incorrect information
          </Link>
        </section>
      </article>
    </main>
  );
}
