import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(request: NextRequest) {
  // Read straight from the incoming request to avoid any runtime or cache issues.
  const token = request.cookies.get("fas_token")?.value;

  if (!token) {
    return NextResponse.json({ authenticated: false }, { status: 401 });
  }

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 2000);

    const res = await fetch(`${process.env.FASTAPI_BASE_URL || "http://localhost:8000"}/agent-actions/?limit=1`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: controller.signal,
    });
    clearTimeout(timeout);

    if (res.status === 401) {
      return NextResponse.json({ authenticated: false }, { status: 401, headers: { "Cache-Control": "no-store" } });
    }

    if (!res.ok) {
      console.error("Auth session validation upstream error:", res.status, await res.text());
      return NextResponse.json({ authenticated: false, error: "upstream_unavailable" }, { status: 503, headers: { "Cache-Control": "no-store" } });
    }

    return NextResponse.json({ authenticated: true }, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    console.error("Auth session validation failed:", error);
    return NextResponse.json({ authenticated: false, error: "validation_error" }, { status: 503, headers: { "Cache-Control": "no-store" } });
  }
}
