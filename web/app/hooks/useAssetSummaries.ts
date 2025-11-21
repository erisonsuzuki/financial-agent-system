"use client";

import { useQuery } from "@tanstack/react-query";

export type AssetSummary = {
  id: number;
  name: string;
  ticker: string;
  units: number;
  averagePrice: number;
};

export function useAssetSummaries(isAuthenticated: boolean) {
  return useQuery({
    queryKey: ["assets-summary", isAuthenticated ? "auth" : "guest"],
    queryFn: async () => {
      const res = await fetch("/api/assets-summary", { cache: "no-store", credentials: "include" });
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
