"use client";

import { useQuery } from "@tanstack/react-query";

export type AssetSummary = {
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

export function useAssetSummaries(isAuthenticated: boolean, refresh: boolean = false) {
  return useQuery({
    queryKey: ["assets-summary", isAuthenticated ? "auth" : "guest", refresh ? "refresh" : "default"],
    queryFn: async () => {
      const query = refresh ? "?refresh=true" : "";
      const res = await fetch(`/api/assets-summary${query}`, { cache: "no-store", credentials: "include" });
      if (res.status === 401) {
        throw new Error("Session expired");
      }
      if (!res.ok) {
        throw new Error("Unable to load assets");
      }
      return res.json() as Promise<AssetSummary[]>;
    },
    staleTime: 60_000,
    gcTime: 5 * 60_000,
  });
}
