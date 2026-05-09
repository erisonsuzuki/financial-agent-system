import { NextRequest, NextResponse } from "next/server";
import { fastapiFetch } from "@/app/lib/fas-api";

export async function POST(request: NextRequest) {
  const origin = request.headers.get("origin");
  const host = request.headers.get("host");
  if (origin && host) {
    const requestOrigin = new URL(origin);
    if (requestOrigin.host !== host) {
      return NextResponse.json({ detail: "Invalid origin" }, { status: 403 });
    }
  }

  const payload = await request.json();
  const setupToken = request.cookies.get("fas_setup_token")?.value;
  if (!setupToken) {
    return NextResponse.json({ detail: "Missing setup token" }, { status: 401 });
  }

  const data = await fastapiFetch<{ access_token: string }>("/auth/register/magic-link/set-password", {
    method: "POST",
    body: JSON.stringify({
      setup_token: setupToken,
      password: payload.password,
    }),
  });

  const response = NextResponse.json({ ok: true });
  response.cookies.delete("fas_setup_token");
  response.cookies.set("fas_token", data.access_token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60,
  });
  return response;
}
