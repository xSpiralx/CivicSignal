export function SafetyNotice() {
  const emergency =
    process.env.NEXT_PUBLIC_EMERGENCY_MESSAGE ??
    "Call 911 for immediate danger.";
  return (
    <aside
      aria-label="Safety notice"
      className="glass-subtle rounded-[1.4rem] border-l-4 border-[var(--urgent)] p-5"
    >
      <p className="font-bold text-[var(--urgent)]">{emergency}</p>
      <p className="mt-2 text-sm">
        CivicSignal does not replace emergency services and cannot guarantee
        availability. Information changes; confirm time-sensitive details
        directly with the provider.
      </p>
    </aside>
  );
}
