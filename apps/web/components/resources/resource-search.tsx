"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { ResourceCard } from "./resource-card";
import type { Category, ServiceList } from "@/lib/resources";

export function ResourceSearch() {
  const [results, setResults] = useState<ServiceList | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [params, setParams] = useState(() => new URLSearchParams());
  const requestSequence = useRef(0);

  async function load(next: URLSearchParams) {
    const request = ++requestSequence.current;
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`/api/resources/services?${next}`);
      if (!response.ok) throw new Error("Request failed");
      const data = (await response.json()) as ServiceList;
      if (request !== requestSequence.current) return;
      setResults(data);
      setParams(next);
      window.history.replaceState(null, "", `/resources?${next}`);
    } catch {
      if (request === requestSequence.current)
        setError("We could not load resources. Please try again.");
    } finally {
      if (request === requestSequence.current) setLoading(false);
    }
  }

  useEffect(() => {
    const initial = new URLSearchParams(window.location.search);
    const request = ++requestSequence.current;
    void fetch(`/api/resources/services?${initial}`)
      .then((response) => {
        if (!response.ok) throw new Error("Request failed");
        return response.json() as Promise<ServiceList>;
      })
      .then((data) => {
        if (request !== requestSequence.current) return;
        setResults(data);
        setParams(initial);
        setLoading(false);
      })
      .catch(() => {
        if (request !== requestSequence.current) return;
        setError("We could not load resources. Please try again.");
        setLoading(false);
      });
    void fetch("/api/resources/categories")
      .then((response) => (response.ok ? response.json() : []))
      .then((data: Category[]) =>
        setCategories(Array.isArray(data) ? data : []),
      )
      .catch(() => setCategories([]));
  }, []);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const next = new URLSearchParams();
    for (const key of [
      "q",
      "category",
      "city",
      "state",
      "postal_code",
      "language",
      "accessibility",
    ]) {
      const value = String(data.get(key) ?? "").trim();
      if (value) next.set(key, value);
    }
    void load(next);
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[19rem_1fr]">
      <form
        onSubmit={submit}
        aria-label="Resource filters"
        className="glass self-start rounded-[1.7rem] p-5 lg:sticky lg:top-28"
      >
        <label className="font-bold" htmlFor="q">
          What do you need?
        </label>
        <input
          className="mt-2 min-h-12 w-full rounded-2xl border border-white/90 bg-white/65 px-4 shadow-inner"
          id="q"
          name="q"
          maxLength={200}
          defaultValue={params.get("q") ?? ""}
        />
        <label className="mt-4 block font-bold" htmlFor="category">
          Category
        </label>
        <select
          className="mt-2 min-h-12 w-full rounded-2xl border border-white/90 bg-white/65 px-4 shadow-inner"
          id="category"
          name="category"
          defaultValue={params.get("category") ?? ""}
        >
          <option value="">All categories</option>
          {categories.map((category) => (
            <option key={category.slug} value={category.slug}>
              {category.name}
            </option>
          ))}
        </select>
        {[
          ["city", "City"],
          ["state", "State or region"],
          ["postal_code", "Postal code"],
          ["language", "Language"],
          ["accessibility", "Accessibility need"],
        ].map(([name, label]) => (
          <div key={name}>
            <label className="mt-4 block font-bold" htmlFor={name}>
              {label}
            </label>
            <input
              className="mt-2 min-h-12 w-full rounded-2xl border border-white/90 bg-white/65 px-4 shadow-inner"
              id={name}
              name={name}
              maxLength={120}
              defaultValue={params.get(name) ?? ""}
            />
          </div>
        ))}
        <button
          className="liquid-button mt-5 min-h-12 w-full rounded-full bg-gradient-to-b from-[#2987eb] to-[#1767cf] px-4 font-bold text-white"
          type="submit"
        >
          Search resources
        </button>
        <button
          className="mt-2 min-h-12 w-full rounded-full border border-white/90 bg-white/55 px-4 font-bold text-[var(--teal-dark)]"
          type="reset"
          onClick={() => void load(new URLSearchParams())}
        >
          Clear filters
        </button>
      </form>
      <section aria-labelledby="results-heading" aria-busy={loading}>
        <p className="eyebrow">Source-aware directory</p>
        <h1
          id="results-heading"
          className="mt-2 text-4xl font-extrabold tracking-tight sm:text-5xl"
        >
          Community resources
        </h1>
        <div aria-live="polite" className="mt-2 min-h-7 text-[var(--muted)]">
          {loading
            ? "Loading resources…"
            : error || `${results?.pagination.total ?? 0} resources found`}
        </div>
        {!loading && !error && results?.items.length === 0 && (
          <div className="glass-subtle mt-6 rounded-[1.5rem] p-7">
            <h2 className="font-bold">No matching resources</h2>
            <p>Try removing a filter or using a broader term.</p>
          </div>
        )}
        {error && (
          <div
            role="alert"
            className="mt-6 rounded-[1.5rem] border border-red-300 bg-red-50/90 p-5 shadow-sm"
          >
            {error}
          </div>
        )}
        <div className="mt-5 grid gap-5">
          {results?.items.map((service) => (
            <ResourceCard key={service.id} service={service} />
          ))}
        </div>
        {results && results.pagination.total_pages > 1 && (
          <nav aria-label="Resource results pages" className="mt-6 flex gap-3">
            <button
              disabled={results.pagination.page <= 1}
              className="min-h-11 rounded-lg border px-4 disabled:opacity-50"
              onClick={() => {
                const next = new URLSearchParams(params);
                next.set("page", String(results.pagination.page - 1));
                void load(next);
              }}
            >
              Previous
            </button>
            <span className="py-2">
              Page {results.pagination.page} of {results.pagination.total_pages}
            </span>
            <button
              disabled={
                results.pagination.page >= results.pagination.total_pages
              }
              className="min-h-11 rounded-lg border px-4 disabled:opacity-50"
              onClick={() => {
                const next = new URLSearchParams(params);
                next.set("page", String(results.pagination.page + 1));
                void load(next);
              }}
            >
              Next
            </button>
          </nav>
        )}
      </section>
    </div>
  );
}
