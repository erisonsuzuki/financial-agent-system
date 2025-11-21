import { NextRequest, NextResponse } from "next/server";
import { fastapiFetch } from "@/app/lib/fas-api";

type Asset = { id: number; ticker: string; name: string };
type AssetAnalysis = { total_quantity: number; average_price: string };
type AssetSummary = {
  id: number;
  name: string;
  ticker: string;
  units: number;
  averagePrice: number;
  error?: string;
};

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(request: NextRequest) {
  const token = request.cookies.get("fas_token")?.value;
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
        try {
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
        } catch (error) {
          console.error(`Failed to fetch analysis for ${asset.ticker}:`, error);
          return {
            id: asset.id,
            name: asset.name,
            ticker: asset.ticker,
            units: 0,
            averagePrice: 0,
            error: "analysis_unavailable",
          };
        }
      })
    );

    return NextResponse.json(enriched);
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: `Failed to load assets: ${message}` }, { status: 502 });
  }
}
