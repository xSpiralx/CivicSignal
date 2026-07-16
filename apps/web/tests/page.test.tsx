import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import Home from "@/app/page";

vi.mock("@/components/health-status", () => ({
  HealthStatus: () => <div>Checking service status…</div>,
}));

describe("Home", () => {
  it("shows the service purpose and emergency disclaimer", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Find community support with clarity and care",
    );
    expect(
      screen.getByText("Call 911 for immediate danger."),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/does not replace emergency services/i),
    ).toBeInTheDocument();
  });

  it("provides a main-content target for keyboard navigation", () => {
    render(<Home />);
    expect(screen.getByRole("main")).toHaveAttribute("id", "main-content");
  });
});
