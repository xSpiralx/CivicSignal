"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AdminShell } from "@/components/admin/admin-shell";
import { adminFetch } from "@/lib/admin-api";

type Area = { code: string; name: string; candidate_count: number; status: string };
type Coverage = { states: Area[]; territories: Area[] };

export default function CoveragePage() {
  const [coverage, setCoverage] = useState<Coverage | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { adminFetch<Coverage>("imports/coverage").then(setCoverage).catch((cause) => setError(cause.message)); }, []);
  return <AdminShell>{() => <div className="grid gap-5"><section className="glass rounded-3xl p-6 sm:p-8"><Link className="text-sm font-bold" href="/admin/import-candidates">← Candidate queue</Link><p className="eyebrow mt-5">Honest source coverage</p><h1 className="mt-2 text-3xl font-extrabold">State and territory coverage</h1><p className="mt-3 max-w-3xl text-[var(--muted)]">A candidate count means this HRSA healthcare source has records for the area. It does not mean CivicSignal has complete community-resource coverage.</p></section>{error && <p className="rounded-2xl bg-red-50 p-4" role="alert">{error}</p>}<section className="glass-subtle rounded-3xl p-5" aria-busy={!coverage}><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{coverage?.states.map((area) => <AreaCard area={area} key={area.code} />)}</div>{coverage && <><h2 className="mt-8 text-xl font-bold">Territories</h2><div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{coverage.territories.map((area) => <AreaCard area={area} key={area.code} />)}</div></>}</section></div>}</AdminShell>;
}

function AreaCard({ area }: { area: Area }) {
  return <div className="rounded-2xl bg-white/80 p-4"><div className="flex items-start justify-between gap-2"><div><h2 className="font-bold">{area.name}</h2><p className="text-sm text-[var(--muted)]">{area.code}</p></div><strong>{area.candidate_count.toLocaleString()}</strong></div><p className="mt-3 text-xs font-bold uppercase text-[var(--muted)]">{area.status.replaceAll("_", " ")}</p></div>;
}
