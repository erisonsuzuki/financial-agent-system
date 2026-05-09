import { NextRequest, NextResponse } from "next/server";
import { fastapiFetch } from "@/app/lib/fas-api";
import type { AgentAction } from "@/app/types/router";

export async function GET(request: NextRequest) {
  const token = request.cookies.get("fas_token")?.value;
  if (!token) {
    return NextResponse.json([], { status: 200 });
  }

  const data = await fastapiFetch<AgentAction[]>("/agent-actions/", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  }).catch(() => []);

  return NextResponse.json(data, { headers: { "Cache-Control": "no-store" } });
}
