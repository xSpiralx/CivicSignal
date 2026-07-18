import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import { ActionDialog } from "@/components/dialogs/action-dialog";

function Harness({ submit = vi.fn() }: { submit?: () => void }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button onClick={() => setOpen(true)}>Open action</button>
      <ActionDialog
        open={open}
        title="Archive resource?"
        description="This removes it from public results."
        submitLabel="Archive resource"
        destructive
        onClose={() => setOpen(false)}
        onSubmit={submit}
      >
        <label>
          Required reason
          <textarea required autoFocus />
        </label>
        <label>
          <input type="checkbox" required /> I understand
        </label>
      </ActionDialog>
    </>
  );
}

describe("ActionDialog", () => {
  it("labels the modal, focuses its first field, traps focus, and restores focus", async () => {
    render(<Harness />);
    const trigger = screen.getByRole("button", { name: "Open action" });
    trigger.focus();
    fireEvent.click(trigger);
    const dialog = screen.getByRole("dialog", { name: "Archive resource?" });
    expect(dialog).toHaveAttribute("aria-modal", "true");
    const reason = screen.getByRole("textbox", { name: "Required reason" });
    await waitFor(() => expect(reason).toHaveFocus());
    const submitButton = screen.getByRole("button", {
      name: "Archive resource",
    });
    submitButton.focus();
    fireEvent.keyDown(submitButton, { key: "Tab" });
    expect(reason).toHaveFocus();
    fireEvent.keyDown(dialog, { key: "Escape" });
    await waitFor(() => expect(trigger).toHaveFocus());
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("supports keyboard form submission with native validation fields", async () => {
    const submit = vi.fn();
    render(<Harness submit={submit} />);
    fireEvent.click(screen.getByRole("button", { name: "Open action" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Required reason" }), {
      target: { value: "Verified closure evidence" },
    });
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.submit(
      screen.getByRole("button", { name: "Archive resource" }).closest("form")!,
    );
    expect(submit).toHaveBeenCalledOnce();
  });
});
