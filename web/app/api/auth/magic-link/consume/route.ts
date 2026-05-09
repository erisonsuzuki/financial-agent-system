import { NextRequest, NextResponse } from "next/server";
import { fastapiFetch } from "@/app/lib/fas-api";

interface ConsumeResponse {
  requires_password_setup: boolean;
  access_token?: string;
  token_type?: string;
  setup_token?: string;
}

export async function POST(request: NextRequest) {
  const payload = await request.json();
  const data = await fastapiFetch<ConsumeResponse>("/auth/register/magic-link/consume", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  const response = NextResponse.json(data);
  if (data.requires_password_setup && data.setup_token) {
    response.cookies.set("fas_setup_token", data.setup_token, {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      path: "/",
      maxAge: 10 * 60,
    });
    return response;
  }

  if (data.access_token) {
    response.cookies.set("fas_token", data.access_token, {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      path: "/",
      maxAge: 60 * 60,
    });
  }

  return response;
}
