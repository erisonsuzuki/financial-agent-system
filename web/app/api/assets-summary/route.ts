import { NextRequest, NextResponse } from "next/server";
import { fastapiFetch } from "@/app/lib/fas-api";

type BackendAssetSummary = {
  id: number;
  name: string;
  ticker: string;
  units: number;
  average_price: string;
  current_price: string | null;
  pl_value: string | null;
  pl_percent: string | null;
  dividends: string;
  total_return_value: string | null;
  total_return_percent: string | null;
  price_fetched_at: string | null;
  is_stale: boolean;
  error?: string | null;
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
    const summaryPath = refresh ? "/assets/summary?refresh=true" : "/assets/summary";
    const assets = await fastapiFetch<BackendAssetSummary[]>(summaryPath, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!assets.length) {
      return NextResponse.json([]);
    }

    const enriched: AssetSummary[] = assets.map((asset) => ({
      id: asset.id,
      name: asset.name,
      ticker: asset.ticker,
      units: asset.units,
      averagePrice: Number(asset.average_price),
      currentPrice: asset.current_price ? Number(asset.current_price) : null,
      plValue: asset.pl_value ? Number(asset.pl_value) : null,
      plPercent: asset.pl_percent ? Number(asset.pl_percent) : null,
      dividends: Number(asset.dividends),
      totalReturnValue: asset.total_return_value ? Number(asset.total_return_value) : null,
      totalReturnPercent: asset.total_return_percent ? Number(asset.total_return_percent) : null,
      priceFetchedAt: asset.price_fetched_at,
      isStale: asset.is_stale,
      error: asset.error ?? undefined,
    }));

    return NextResponse.json(enriched);
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: `Failed to load assets: ${message}` }, { status: 502 });
  }
}
