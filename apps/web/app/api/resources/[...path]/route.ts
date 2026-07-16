import { NextRequest, NextResponse } from "next/server";
import { internalApiBase } from "@/lib/server-api";

export const dynamic = "force-dynamic";

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const apiUrl = internalApiBase();
  const target = new URL(
    `${apiUrl}/api/v1/${path.map(encodeURIComponent).join("/")}`,
  );
  request.nextUrl.searchParams.forEach((value, key) =>
    target.searchParams.append(key, value),
  );
  try {
    const response = await fetch(target, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
    const body: unknown = await response.json();
    return NextResponse.json(body, { status: response.status });
  } catch {
    return NextResponse.json(
      {
        error: {
          code: "upstream_unavailable",
          message: "Resource service unavailable",
        },
      },
      { status: 503 },
    );
  }
}
