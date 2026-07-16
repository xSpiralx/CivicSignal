"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { AdminShell } from "@/components/admin/admin-shell";
import { Account, adminFetch } from "@/lib/admin-api";

export default function NewAccountPage() {
  return <AdminShell>{() => <NewAccount />}</AdminShell>;
}
function NewAccount() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    const data = new FormData(event.currentTarget);
    try {
      const account = await adminFetch<Account>("accounts", {
        method: "POST",
        body: JSON.stringify({
          email: data.get("email"),
          display_name: data.get("display_name"),
          password: data.get("password"),
          roles: data.getAll("roles"),
        }),
      });
      router.push(`/admin/accounts/${account.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to create account");
      setBusy(false);
    }
  }
  return (
    <section className="glass max-w-2xl rounded-3xl p-6 sm:p-8">
      <p className="eyebrow">Access control</p>
      <h1 className="mt-2 text-3xl font-extrabold">
        Create administrator account
      </h1>
      {error && (
        <p role="alert" className="mt-4 rounded-xl bg-red-50 p-3 text-red-900">
          {error}
        </p>
      )}
      <form className="mt-6 grid gap-5" onSubmit={submit}>
        <Field label="Display name" name="display_name" autoComplete="name" />
        <Field
          label="Email"
          name="email"
          type="email"
          autoComplete="username"
        />
        <Field
          label="Initial password"
          name="password"
          type="password"
          autoComplete="new-password"
        />
        <fieldset>
          <legend className="font-bold">Roles</legend>
          <div className="mt-2 grid gap-2 sm:grid-cols-2">
            {[
              "viewer",
              "contributor",
              "reviewer",
              "verifier",
              "administrator",
            ].map((role) => (
              <label className="rounded-xl bg-white/75 p-3" key={role}>
                <input
                  className="mr-2"
                  name="roles"
                  type="checkbox"
                  value={role}
                />
                {role}
              </label>
            ))}
          </div>
        </fieldset>
        <button
          className="rounded-2xl bg-[#176d83] px-5 py-3 font-bold text-white"
          disabled={busy}
        >
          {busy ? "Creating…" : "Create account"}
        </button>
      </form>
    </section>
  );
}
function Field({
  label,
  name,
  type = "text",
  autoComplete,
}: {
  label: string;
  name: string;
  type?: string;
  autoComplete: string;
}) {
  return (
    <label className="grid gap-2 font-bold">
      {label}
      <input
        autoComplete={autoComplete}
        className="rounded-2xl border bg-white px-4 py-3"
        name={name}
        required
        type={type}
      />
    </label>
  );
}
