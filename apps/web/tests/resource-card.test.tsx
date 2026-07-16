import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ResourceCard } from "@/components/resources/resource-card";

const service = {
  id: "service-1",
  organization_name: "Example Organization",
  name: "Food Support",
  description: "Provides food support.",
  categories: [{ slug: "food", name: "Food assistance", description: null }],
  location_summary: "Exampleville, EX",
  languages: ["English"],
  accessibility: "Wheelchair accessible",
  primary_contact: {
    channel_type: "phone",
    label: "Phone",
    value: "555-0100",
    is_primary: true,
  },
  verification: {
    status: "verified" as const,
    last_checked_at: "2026-07-01T00:00:00Z",
    may_be_stale: false,
    next_due_at: "2026-10-01T00:00:00Z",
    freshness: "current" as const,
  },
};

describe("ResourceCard", () => {
  it("renders contact, source check, and accessible details link", () => {
    render(<ResourceCard service={service} />);
    expect(
      screen.getByRole("heading", { name: "Food Support" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/source checked/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "View details" })).toHaveAttribute(
      "href",
      "/resources/service-1",
    );
  });
});
