import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { HealthStatus } from "@/components/health-status";

afterEach(() => vi.restoreAllMocks());

describe("HealthStatus", () => {
  it("shows an available state", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
    render(<HealthStatus />);
    expect(
      await screen.findByText("Core service is available"),
    ).toBeInTheDocument();
  });

  it("shows an explicit error state", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("network error")),
    );
    render(<HealthStatus />);
    expect(
      await screen.findByText("Core service is temporarily unavailable"),
    ).toBeInTheDocument();
  });
});
