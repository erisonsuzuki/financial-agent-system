"use server";

import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { fastapiFetch } from "@/app/lib/fas-api";

type Asset = { id: number; ticker: string; name: string };
type AssetAnalysis = { total_quantity: number; average_price: string };
type AssetSummary = {
  id: number;
  name: string;
  ticker: string;
  units: number;
  averagePrice: number;
};

export async function GET(_request: NextRequest) {
  const token = (await cookies()).get("fas_token")?.value;
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const assets = await fastapiFetch<Asset[]>("/assets/", {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!assets.length) {
      return NextResponse.json([]);
    }

    const enriched = await Promise.all(
      assets.map(async (asset): Promise<AssetSummary> => {
        const analysis = await fastapiFetch<AssetAnalysis>(`/assets/${asset.ticker}/analysis`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        return {
          id: asset.id,
          name: asset.name,
          ticker: asset.ticker,
          units: analysis.total_quantity,
          averagePrice: Number(analysis.average_price),
        };
      })
    );

    return NextResponse.json(enriched);
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: `Failed to load assets: ${message}` }, { status: 502 });
  }
}
