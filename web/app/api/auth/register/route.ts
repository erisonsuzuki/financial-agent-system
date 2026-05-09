import { NextRequest, NextResponse } from "next/server";
import { fastapiFetch } from "@/app/lib/fas-api";

export async function POST(request: NextRequest) {
  const payload = await request.json();
  const data = await fastapiFetch<{ message: string }>("/auth/register/magic-link", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return NextResponse.json(data, { status: 202 });
}
