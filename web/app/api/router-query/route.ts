import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { fastapiFetch } from "@/app/lib/fas-api";
import type { RouterResponse } from "@/app/types/router";

export async function POST(request: NextRequest) {
  const { question } = await request.json();
  const cookieStore = await cookies();
  const token = cookieStore.get("fas_token")?.value;
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const data = await fastapiFetch<RouterResponse>("/agent/query/router", {
    method: "POST",
    body: JSON.stringify({ question }),
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return NextResponse.json(data);
}
