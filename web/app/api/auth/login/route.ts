import { NextRequest, NextResponse } from "next/server";
import { fastapiFetch } from "@/app/lib/fas-api";

export async function POST(request: NextRequest) {
  const payload = await request.json();
  const data = await fastapiFetch<{ access_token: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  const response = NextResponse.json(data);
  response.cookies.set("fas_token", data.access_token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60,
  });
  return response;
}
