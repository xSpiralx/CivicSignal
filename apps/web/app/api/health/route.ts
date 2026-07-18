import { NextResponse } from "next/server";
import { internalApiBase } from "@/lib/server-api";

export const dynamic = "force-dynamic";

export async function GET() {
  const apiUrl = internalApiBase();
  try {
    const response = await fetch(`${apiUrl}/health/ready`, {
      headers: {
        "x-civicsignal-proxy": process.env.PROXY_SHARED_SECRET ?? "",
      },
      cache: "no-store",
      signal: AbortSignal.timeout(3000),
    });
    return NextResponse.json(
      { status: response.ok ? "available" : "unavailable" },
      { status: response.ok ? 200 : 503 },
    );
  } catch {
    return NextResponse.json({ status: "unavailable" }, { status: 503 });
  }
}
