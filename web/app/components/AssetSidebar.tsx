"use client";

import type { AssetSummary } from "@/app/hooks/useAssetSummaries";
import { formatUtcTimestamp } from "@/app/lib/datetime";

interface Props {
  assets: AssetSummary[] | undefined;
  loading: boolean;
  error: Error | null;
  hideAmounts?: boolean;
  onRefresh?: () => void;
  refreshing?: boolean;
  refreshError?: string | null;
}

function formatCurrency(value: number | null) {
  if (value === null) {
    return "--";
  }
  return `$${value.toFixed(2)}`;
}

function formatPercent(value: number | null) {
  if (value === null) {
    return "--";
  }
  return `${value.toFixed(2)}%`;
}

function formatFetchedAt(value: string | null) {
  return formatUtcTimestamp(value, "Price time unavailable");
}

export default function AssetSidebar({
  assets,
  loading,
  error,
  hideAmounts = false,
  onRefresh,
  refreshing = false,
  refreshError = null,
}: Props) {
  if (loading) {
    return <div className="rounded-xl border border-outline-variant bg-surface-container p-4 text-sm text-on-surface-variant">Loading assets…</div>;
  }
  if (error?.message === "Session expired") {
    return (
      <div className="rounded-xl border border-error-container bg-surface-container p-4 text-sm text-error">
        Session expired. Please{" "}
          <a href="/login" className="underline">
          log in
        </a>{" "}
        again.
      </div>
    );
  }
  if (error) {
    return <div className="rounded-xl border border-error-container bg-surface-container p-4 text-sm text-error">Unable to load assets.</div>;
  }
  if (!assets?.length) {
    return <div className="rounded-xl border border-outline-variant bg-surface-container p-4 text-sm text-on-surface-variant">No assets registered yet.</div>;
  }

  return (
    <section>
      <header className="mb-4 flex items-center justify-between gap-3 px-2">
        <h2 className="font-mono text-xs font-semibold tracking-widest text-neon">REAL-TIME ASSETS</h2>
        {!hideAmounts && onRefresh && (
          <button
            type="button"
            onClick={onRefresh}
            disabled={refreshing}
            className="rounded-full border border-outline-variant px-3 py-1.5 font-mono text-[11px] font-medium tracking-wide text-on-surface-variant hover:border-neon hover:text-neon disabled:cursor-not-allowed disabled:opacity-50"
          >
            {refreshing ? "Refreshing..." : "Refresh prices"}
          </button>
        )}
      </header>
      {!hideAmounts && refreshError && (
        <p className="mb-3 rounded-md border border-error-container bg-error-container/20 px-2 py-1 text-xs text-error">{refreshError}</p>
      )}
      <div className="overflow-x-auto rounded-xl border border-outline-variant bg-surface-container">
        <table className="min-w-[680px] w-full border-collapse text-left">
          <thead className="border-b border-outline-variant bg-surface-high/50 font-mono text-[10px] font-semibold tracking-widest text-on-surface-variant">
            <tr>
              <th className="px-3 py-3">ASSET</th>
              {!hideAmounts && <th className="px-3 py-3 text-right">UNITS</th>}
              {!hideAmounts && <th className="px-3 py-3 text-right">AVG PRICE</th>}
              {!hideAmounts && <th className="px-3 py-3 text-right">CURRENT PRICE</th>}
              {!hideAmounts && <th className="px-3 py-3 text-right">PRICE RETURN</th>}
              {!hideAmounts && <th className="px-3 py-3 text-right">TOTAL PERFORMANCE</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant/50">
            {assets.map((asset) => {
              const performanceClass = asset.totalReturnValue !== null && asset.totalReturnValue < 0
                ? "border-error-container/50 bg-error-container/20 text-error"
                : asset.totalReturnValue !== null && asset.totalReturnValue > 0
                  ? "border-neon/30 bg-neon/10 text-neon"
                  : "border-outline-variant bg-surface-high text-on-surface-variant";
              const priceReturnClass = asset.plValue !== null && asset.plValue < 0 ? "text-error" : "text-neon";

              return (
                <tr key={asset.id} className="text-sm">
                  <td className="px-3 py-3">
                    <p className="font-semibold text-on-surface">{asset.ticker}</p>
                    <p className="text-[10px] text-on-surface-variant">{asset.name}</p>
                    {asset.error && <p className="mt-1 text-[10px] text-error">Analysis unavailable</p>}
                  </td>
                  {!hideAmounts && <td className="px-3 py-3 text-right font-mono text-xs text-on-surface">{asset.units}</td>}
                  {!hideAmounts && <td className="px-3 py-3 text-right font-mono text-xs font-semibold text-neon">${asset.averagePrice.toFixed(2)}</td>}
                  {!hideAmounts && <td className="px-3 py-3 text-right font-mono text-xs text-on-surface">{formatCurrency(asset.currentPrice)}</td>}
                  {!hideAmounts && <td className={`px-3 py-3 text-right font-mono text-xs font-semibold ${priceReturnClass}`}>{formatCurrency(asset.plValue)} ({formatPercent(asset.plPercent)})</td>}
                  {!hideAmounts && (
                    <td className="px-3 py-3 text-right">
                      <p className={`inline-block rounded border px-2 py-1 font-mono text-xs font-semibold ${performanceClass}`}>{formatCurrency(asset.totalReturnValue)} ({formatPercent(asset.totalReturnPercent)})</p>
                      <p className="mt-1 font-mono text-[9px] text-on-surface-variant">{formatFetchedAt(asset.priceFetchedAt)} {asset.isStale ? "STALE" : ""}</p>
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {hideAmounts && (
        <div className="mt-3 text-xs text-on-surface-variant">
          <a href="/login" className="underline text-on-surface">
            Log in
          </a>{" "}
          to view prices and returns.
        </div>
      )}
    </section>
  );
}
