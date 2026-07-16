import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

async function proxy(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const target = new URL(
    `${process.env.API_INTERNAL_URL ?? "http://localhost:8000"}/api/v1/admin/${path.map(encodeURIComponent).join("/")}`,
  );
  request.nextUrl.searchParams.forEach((value, key) =>
    target.searchParams.append(key, value),
  );
  try {
    const upstream = await fetch(target, {
      method: request.method,
      headers: {
        "content-type":
          request.headers.get("content-type") ?? "application/json",
        cookie: request.headers.get("cookie") ?? "",
        "x-csrf-token": request.headers.get("x-csrf-token") ?? "",
        "x-request-id": request.headers.get("x-request-id") ?? "",
      },
      body:
        request.method === "GET" || request.method === "HEAD"
          ? undefined
          : await request.text(),
      cache: "no-store",
      signal: AbortSignal.timeout(8000),
    });
    const response = new NextResponse(
      upstream.status === 204 ? null : await upstream.text(),
      {
        status: upstream.status,
        headers: {
          "content-type":
            upstream.headers.get("content-type") ?? "application/json",
        },
      },
    );
    const cookie = upstream.headers.get("set-cookie");
    if (cookie) response.headers.set("set-cookie", cookie);
    return response;
  } catch {
    return NextResponse.json(
      {
        error: {
          code: "upstream_unavailable",
          message: "Administrator service unavailable",
        },
      },
      { status: 503 },
    );
  }
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
export const PUT = proxy;
export const DELETE = proxy;
