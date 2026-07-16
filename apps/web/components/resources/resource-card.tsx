import Link from "next/link";
import { formatChecked, type ServiceItem } from "@/lib/resources";

export function ResourceCard({ service }: { service: ServiceItem }) {
  return (
    <article className="glass-subtle group rounded-[1.65rem] p-6 transition duration-200 hover:-translate-y-1 hover:shadow-[0_22px_55px_rgba(42,92,140,.17)]">
      <div className="flex flex-wrap gap-2">
        {service.categories.map((category) => (
          <span
            key={category.slug}
            className="rounded-full border border-white/80 bg-white/65 px-3 py-1 text-xs font-bold text-[var(--teal-dark)]"
          >
            {category.name}
          </span>
        ))}
      </div>
      <h2 className="mt-4 text-xl font-extrabold tracking-tight sm:text-2xl">
        <Link
          className="underline decoration-transparent underline-offset-4 hover:decoration-current"
          href={`/resources/${service.id}`}
        >
          {service.name}
        </Link>
      </h2>
      <p className="text-sm font-semibold text-[var(--muted)]">
        {service.organization_name}
      </p>
      <p className="mt-3">{service.description}</p>
      {service.location_summary && (
        <p className="mt-3 text-sm">
          <strong>Area:</strong> {service.location_summary}
        </p>
      )}
      {service.primary_contact && (
        <p className="mt-2 text-sm">
          <strong>{service.primary_contact.label}:</strong>{" "}
          {service.primary_contact.value}
        </p>
      )}
      <div className="mt-5 border-t border-white/80 pt-4 text-sm">
        <p>
          <strong>
            {service.verification.may_be_stale
              ? "Re-verification needed"
              : "Source checked"}
          </strong>{" "}
          · {formatChecked(service.verification.last_checked_at)}
        </p>
        <Link
          className="liquid-button mt-4 inline-block min-h-11 rounded-full bg-gradient-to-b from-[#168b98] to-[#08707d] px-5 py-2.5 font-bold text-white"
          href={`/resources/${service.id}`}
        >
          View details
        </Link>
      </div>
    </article>
  );
}
