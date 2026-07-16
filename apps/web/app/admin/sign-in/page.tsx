"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { adminFetch, loadSession, setCsrf } from "@/lib/admin-api";

export default function SignInPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (new URLSearchParams(window.location.search).has("expired"))
      setError("Your session ended. Sign in again to continue.");
    loadSession()
      .then(() => router.replace("/admin"))
      .catch(() => undefined);
  }, [router]);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const data = new FormData(event.currentTarget);
    try {
      const session = await adminFetch<{ csrf_token: string }>("auth/sign-in", {
        method: "POST",
        body: JSON.stringify({
          email: data.get("email"),
          password: data.get("password"),
        }),
      });
      setCsrf(session.csrf_token);
      router.replace("/admin");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Sign-in failed");
      setBusy(false);
    }
  }
  return (
    <main className="grid min-h-screen place-items-center px-4 py-12">
      <section className="glass w-full max-w-md rounded-[2rem] p-7 sm:p-9">
        <p className="eyebrow">Administrator access</p>
        <h1 className="mt-3 text-3xl font-extrabold">Sign in to CivicSignal</h1>
        <p className="mt-2 text-[var(--muted)]">
          Authorized maintainers only. Your session is protected by a secure
          server-managed cookie.
        </p>
        {error && (
          <div
            role="alert"
            className="mt-5 rounded-2xl border border-red-200 bg-red-50 p-3 text-sm text-red-900"
          >
            {error}
          </div>
        )}
        <form className="mt-6 grid gap-5" onSubmit={submit}>
          <label className="grid gap-2 font-semibold">
            Email
            <input
              autoComplete="username"
              className="rounded-2xl border border-[#b7ced8] bg-white px-4 py-3"
              name="email"
              required
              type="email"
            />
          </label>
          <label className="grid gap-2 font-semibold">
            Password
            <input
              autoComplete="current-password"
              className="rounded-2xl border border-[#b7ced8] bg-white px-4 py-3"
              name="password"
              required
              type="password"
            />
          </label>
          <button
            className="liquid-button rounded-2xl bg-[#176d83] px-5 py-3 font-bold text-white disabled:opacity-60"
            disabled={busy}
          >
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <Link className="mt-6 inline-block font-semibold" href="/">
          ← Return to public resources
        </Link>
      </section>
    </main>
  );
}
