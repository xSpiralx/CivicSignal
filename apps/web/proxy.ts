import { timingSafeEqual } from "node:crypto";
import { NextRequest, NextResponse } from "next/server";

function sameSecret(actual: string, expected: string): boolean {
  const left = Buffer.from(actual);
  const right = Buffer.from(expected);
  return left.length === right.length && timingSafeEqual(left, right);
}

export function proxy(request: NextRequest) {
  if (process.env.NEXT_PUBLIC_APP_ENV !== "staging") return NextResponse.next();
  const username = process.env.STAGING_ACCESS_USERNAME;
  const password = process.env.STAGING_ACCESS_PASSWORD;
  if (!username || !password) {
    return new NextResponse("Staging access is not configured.", {
      status: 503,
    });
  }
  const header = request.headers.get("authorization");
  if (header?.startsWith("Basic ")) {
    try {
      const decoded = Buffer.from(header.slice(6), "base64").toString("utf8");
      const separator = decoded.indexOf(":");
      if (
        separator > 0 &&
        sameSecret(decoded.slice(0, separator), username) &&
        sameSecret(decoded.slice(separator + 1), password)
      )
        return NextResponse.next();
    } catch {}
  }
  return new NextResponse("Private CivicSignal staging environment", {
    status: 401,
    headers: {
      "WWW-Authenticate": 'Basic realm="CivicSignal Staging", charset="UTF-8"',
      "Cache-Control": "no-store",
    },
  });
}

export const config = {
  matcher: ["/((?!api/health|_next/static|_next/image|favicon.ico).*)"],
};
