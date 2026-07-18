import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import CorrectionPage from "@/app/resources/[id]/report/page";

vi.mock("next/navigation", () => ({ useParams: () => ({ id: "service-1" }) }));

const resource = {
  id: "service-1",
  name: "Example food support",
  description: "Fictional resource",
  eligibility: null,
  required_documents: null,
  cost_information: null,
  languages: ["English"],
  accessibility: null,
  application_instructions: null,
  appointment_requirements: null,
  emergency_availability: false,
  organization: {
    public_name: "Example Organization",
    website: null,
    public_phone: null,
    public_email: null,
  },
  categories: [],
  locations: [],
  contacts: [],
  sources: [],
  verification: {
    status: "verified",
    last_checked_at: "2026-07-01T00:00:00Z",
    may_be_stale: false,
    next_due_at: "2026-10-01T00:00:00Z",
    freshness: "current",
  },
};

afterEach(() => vi.restoreAllMocks());

describe("Correction report", () => {
  it("shows resource context, privacy guidance, and a safe success state", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(JSON.stringify(resource), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: "report-1", status: "received" }), {
          status: 202,
        }),
      );
    render(<CorrectionPage />);
    expect(await screen.findByText("Example food support")).toBeInTheDocument();
    expect(screen.getByText(/Protect your privacy/i)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("What needs attention?"), {
      target: { value: "incorrect_hours" },
    });
    fireEvent.change(
      screen.getByRole("textbox", { name: /What appears incorrect/i }),
      {
        target: { value: "The Saturday hours appear incorrect." },
      },
    );
    fireEvent.submit(
      screen.getByRole("button", { name: "Submit report" }).closest("form")!,
    );
    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent("Report received"),
    );
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
