import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ProposedRevisionEditor } from "@/components/admin/proposed-revision-editor";
import {
  adminFetch,
  DraftContent,
  Proposal,
  ReverificationTask,
} from "@/lib/admin-api";

vi.mock("@/lib/admin-api", async (original) => ({
  ...(await original<typeof import("@/lib/admin-api")>()),
  adminFetch: vi.fn(),
}));
const content: DraftContent = {
  organization_name: "Example Organization",
  organization_description: "Fictional",
  organization_type: "nonprofit",
  service_name: "Example support",
  description: "Fictional support",
  eligibility: "Residents",
  required_documents: null,
  cost_information: null,
  languages: ["English"],
  accessibility: "Accessible",
  emergency_availability: false,
  remote_service_available: false,
  categories: ["Support"],
  contact_phone: "555-0100",
  contact_email: null,
  website: "https://provider.example",
  location_name: null,
  city: null,
  region: null,
  postal_code: null,
  country: "US",
  timezone: null,
  service_area: "Example County",
  hours: "9–5",
  transportation: null,
  application_instructions: null,
  source_name: "Provider page",
  source_url: "https://provider.example/source",
  source_organization: "Example Organization",
  source_type: "provider_submission",
  source_retrieved_at: null,
  source_notes: null,
  source_public: true,
  source_supports_changed_fields: true,
};
const task: ReverificationTask = {
  id: "task-1",
  service_id: "service-1",
  resource_id: "resource-1",
  published_revision_id: "revision-1",
  trigger_source: "public_correction",
  reason: "hours",
  freshness_state: "reported_change",
  due_at: "2026-08-01T00:00:00Z",
  status: "in_progress",
  assigned_verifier_id: "account-1",
  claimed_at: null,
  started_at: null,
  completed_at: null,
  outcome: null,
  evidence_summary: null,
  contact_attempt_summary: null,
  source_references: null,
  notes: null,
  version: 1,
  created_at: "2026-07-18T00:00:00Z",
};
const proposal: Proposal = {
  task_id: "task-1",
  task_version: 1,
  resource_id: "resource-1",
  published_revision: 1,
  proposed_revision: 1,
  published_content: content,
  proposed_content: content,
  changed_fields: [],
  blocking_errors: [],
  warnings: ["No changes"],
  ready: false,
};

describe("ProposedRevisionEditor", () => {
  it("loads published content, edits structured fields, and saves an immutable proposal", async () => {
    const saved = {
      ...proposal,
      task_version: 2,
      proposed_revision: 2,
      proposed_content: { ...content, hours: "9–6" },
      changed_fields: ["hours"],
      warnings: [],
      ready: true,
    };
    vi.mocked(adminFetch)
      .mockResolvedValueOnce(proposal)
      .mockResolvedValueOnce(saved);
    const changed = vi.fn();
    render(<ProposedRevisionEditor task={task} onTaskChange={changed} />);
    expect(
      await screen.findByDisplayValue("Example support"),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Hours"), {
      target: { value: "9–6" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Save proposed revision" }),
    );
    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent(
        "Saved as revision 2",
      ),
    );
    expect(adminFetch).toHaveBeenLastCalledWith(
      "reverification/task-1/proposal",
      expect.objectContaining({ method: "POST" }),
    );
    expect(changed).toHaveBeenCalledWith(
      expect.objectContaining({ version: 2 }),
    );
    expect(screen.getByText("Published versus proposed")).toBeInTheDocument();
  });
});
