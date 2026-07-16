import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ResourceSearch } from "@/components/resources/resource-search";

afterEach(() => vi.restoreAllMocks());
const empty = {
  items: [],
  pagination: { page: 1, page_size: 20, total: 0, total_pages: 0 },
};

function successfulFetch() {
  return vi.fn().mockImplementation((input: string) =>
    Promise.resolve({
      ok: true,
      json: async () => (input.includes("categories") ? [] : empty),
    }),
  );
}

describe("ResourceSearch", () => {
  it("renders loading and empty states", async () => {
    vi.stubGlobal("fetch", successfulFetch());
    render(<ResourceSearch />);
    expect(screen.getByText("Loading resources…")).toBeInTheDocument();
    expect(
      await screen.findByText("No matching resources"),
    ).toBeInTheDocument();
  });

  it("submits search and filters", async () => {
    const fetchMock = successfulFetch();
    vi.stubGlobal("fetch", fetchMock);
    render(<ResourceSearch />);
    await screen.findByText("No matching resources");
    fireEvent.change(screen.getByLabelText("What do you need?"), {
      target: { value: "food" },
    });
    fireEvent.change(screen.getByLabelText("City"), {
      target: { value: "Exampleville" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Search resources" }));
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("q=food")),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("city=Exampleville"),
    );
  });

  it("announces API errors", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<ResourceSearch />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "could not load resources",
    );
  });
});
