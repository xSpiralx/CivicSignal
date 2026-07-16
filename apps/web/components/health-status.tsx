"use client";

import { useEffect, useState } from "react";

type HealthState = "loading" | "available" | "unavailable";

export function HealthStatus() {
  const [state, setState] = useState<HealthState>("loading");

  useEffect(() => {
    const controller = new AbortController();
    async function checkHealth() {
      try {
        const response = await fetch("/api/health", {
          cache: "no-store",
          signal: controller.signal,
        });
        setState(response.ok ? "available" : "unavailable");
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError")
          return;
        setState("unavailable");
      }
    }
    void checkHealth();
    return () => controller.abort();
  }, []);

  const labels: Record<HealthState, string> = {
    loading: "Checking service status…",
    available: "Core service is available",
    unavailable: "Core service is temporarily unavailable",
  };

  return (
    <div
      aria-live="polite"
      aria-atomic="true"
      className="flex items-center gap-3 text-sm"
    >
      <span
        aria-hidden="true"
        className={`h-3 w-3 rounded-full ${
          state === "available"
            ? "bg-emerald-600"
            : state === "unavailable"
              ? "bg-red-700"
              : "animate-pulse bg-slate-400"
        }`}
      />
      <span>{labels[state]}</span>
    </div>
  );
}
