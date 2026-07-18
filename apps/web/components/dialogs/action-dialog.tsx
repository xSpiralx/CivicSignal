"use client";

import { FormEvent, ReactNode, useId, useLayoutEffect, useRef } from "react";

type Props = {
  open: boolean;
  title: string;
  description: string;
  submitLabel: string;
  destructive?: boolean;
  loading?: boolean;
  error?: string;
  children?: ReactNode;
  onClose: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void | Promise<void>;
};

export function ActionDialog({
  open,
  title,
  description,
  submitLabel,
  destructive = false,
  loading = false,
  error,
  children,
  onClose,
  onSubmit,
}: Props) {
  const titleId = useId();
  const descriptionId = useId();
  const panel = useRef<HTMLDivElement>(null);
  const returnFocus = useRef<HTMLElement | null>(null);
  useLayoutEffect(() => {
    if (!open) {
      const rememberFocus = (event: FocusEvent) => {
        returnFocus.current = event.target as HTMLElement | null;
      };
      document.addEventListener("focusin", rememberFocus);
      return () => document.removeEventListener("focusin", rememberFocus);
    }
    const frame = requestAnimationFrame(() =>
      panel.current
        ?.querySelector<HTMLElement>("input, textarea, select, button")
        ?.focus(),
    );
    return () => {
      cancelAnimationFrame(frame);
      returnFocus.current?.focus();
    };
  }, [open]);
  if (!open) return null;
  function keyDown(event: React.KeyboardEvent) {
    if (event.key === "Escape" && !loading) {
      event.preventDefault();
      onClose();
      return;
    }
    if (event.key !== "Tab" || !panel.current) return;
    const controls = [
      ...panel.current.querySelectorAll<HTMLElement>(
        "button:not(:disabled), input:not(:disabled), textarea:not(:disabled), select:not(:disabled), a[href]",
      ),
    ];
    if (!controls.length) return;
    const first = controls[0],
      last = controls[controls.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }
  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center overflow-y-auto bg-[#10243f]/45 p-4"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !loading) onClose();
      }}
    >
      <div
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
        onKeyDown={keyDown}
        className="glass my-auto w-full max-w-xl rounded-[2rem] p-6 sm:p-8"
      >
        <h2 id={titleId} className="text-2xl font-extrabold">
          {title}
        </h2>
        <p id={descriptionId} className="mt-2 text-[var(--muted)]">
          {description}
        </p>
        <form
          className="mt-5 grid gap-4"
          onSubmit={(e) => {
            e.preventDefault();
            void onSubmit(e);
          }}
        >
          {children}
          {error && (
            <p role="alert" className="rounded-xl bg-red-50 p-3">
              {error}
            </p>
          )}
          <div className="flex flex-wrap justify-end gap-3">
            <button
              type="button"
              disabled={loading}
              onClick={onClose}
              className="rounded-full bg-white px-5 py-3 font-bold"
            >
              Cancel
            </button>
            <button
              disabled={loading}
              className={`rounded-full px-5 py-3 font-bold text-white ${destructive ? "bg-[#8f263c]" : "bg-[#176d83]"}`}
            >
              {loading ? "Working…" : submitLabel}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
