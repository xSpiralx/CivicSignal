export function internalApiBase(): string {
  const configured = process.env.API_INTERNAL_URL ?? "http://localhost:8000";
  return configured.startsWith("http://") || configured.startsWith("https://")
    ? configured
    : `http://${configured}`;
}
