import { NextRequest, NextResponse } from "next/server";
import { fastapiFetch } from "@/app/lib/fas-api";

type Asset = { id: number; ticker: string; name: string };
type AssetAnalysis = {
  total_quantity: number;
  average_price: string;
  current_market_price: string | null;
  financial_return_value: string | null;
  financial_return_percent: string | null;
  total_dividends_received?: string | null;
  total_return_value?: string | null;
  total_return_percent?: string | null;
  fetched_at?: string | null;
  is_stale?: boolean;
};
type AssetSummary = {
  id: number;
  name: string;
  ticker: string;
  units: number;
  averagePrice: number;
  currentPrice: number | null;
  plValue: number | null;
  plPercent: number | null;
  dividends: number;
  totalReturnValue: number | null;
  totalReturnPercent: number | null;
  priceFetchedAt: string | null;
  isStale: boolean;
  error?: string;
};

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(request: NextRequest) {
  const token = request.cookies.get("fas_token")?.value;
  const refresh = request.nextUrl.searchParams.get("refresh") === "true";
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
          const analysisPath = refresh
            ? `/assets/${asset.ticker}/analysis?refresh=true`
            : `/assets/${asset.ticker}/analysis`;
          const analysis = await fastapiFetch<AssetAnalysis>(analysisPath, {
            headers: { Authorization: `Bearer ${token}` },
          });
          return {
            id: asset.id,
            name: asset.name,
            ticker: asset.ticker,
            units: analysis.total_quantity,
            averagePrice: Number(analysis.average_price),
            currentPrice: analysis.current_market_price ? Number(analysis.current_market_price) : null,
            plValue: analysis.financial_return_value ? Number(analysis.financial_return_value) : null,
            plPercent: analysis.financial_return_percent ? Number(analysis.financial_return_percent) : null,
            dividends: analysis.total_dividends_received ? Number(analysis.total_dividends_received) : 0,
            totalReturnValue: analysis.total_return_value ? Number(analysis.total_return_value) : null,
            totalReturnPercent: analysis.total_return_percent ? Number(analysis.total_return_percent) : null,
            priceFetchedAt: analysis.fetched_at ?? null,
            isStale: analysis.is_stale ?? false,
          };
        } catch (error) {
          console.error(`Failed to fetch analysis for ${asset.ticker}:`, error);
          return {
            id: asset.id,
            name: asset.name,
            ticker: asset.ticker,
            units: 0,
            averagePrice: 0,
            currentPrice: null,
            plValue: null,
            plPercent: null,
            dividends: 0,
            totalReturnValue: null,
            totalReturnPercent: null,
            priceFetchedAt: null,
            isStale: false,
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
