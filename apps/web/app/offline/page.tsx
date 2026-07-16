export default function OfflinePage() {
  return (
    <main id="main-content" className="mx-auto max-w-2xl px-5 py-20">
      <h1 className="text-3xl font-bold">You are offline</h1>
      <p className="mt-4">
        CivicSignal cannot confirm current resource information while offline.
        Reconnect before relying on availability, hours, or eligibility details.
      </p>
    </main>
  );
}
