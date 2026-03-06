"use client";

import type { AssetSummary } from "@/app/hooks/useAssetSummaries";

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
  if (!value) {
    return "Price time unavailable";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "Price time unavailable";
  }

  return parsed.toLocaleString();
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
    return <div className="rounded-xl border border-slate-800 p-4 text-sm text-slate-400">Loading assets…</div>;
  }
  if (error?.message === "Session expired") {
    return (
      <div className="rounded-xl border border-slate-800 p-4 text-sm text-rose-400">
        Session expired. Please{" "}
        <a href="/login" className="underline text-rose-200">
          log in
        </a>{" "}
        again.
      </div>
    );
  }
  if (error) {
    return <div className="rounded-xl border border-slate-800 p-4 text-sm text-rose-400">Unable to load assets.</div>;
  }
  if (!assets?.length) {
    return <div className="rounded-xl border border-slate-800 p-4 text-sm text-slate-400">No assets registered yet.</div>;
  }

  return (
    <aside className="rounded-xl border border-slate-800 bg-slate-900 p-4 max-h-[420px] overflow-y-auto">
      <header className="flex items-center justify-between mb-3">
        <div className="text-xs uppercase text-slate-400">Assets</div>
        {!hideAmounts && onRefresh && (
          <button
            type="button"
            onClick={onRefresh}
            disabled={refreshing}
            className="rounded-md border border-slate-700 px-2 py-1 text-xs font-medium text-slate-200 hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {refreshing ? "Refreshing..." : "Refresh prices"}
          </button>
        )}
      </header>
      {!hideAmounts && refreshError && (
        <p className="mb-3 rounded-md border border-rose-700 bg-rose-950/40 px-2 py-1 text-xs text-rose-300">{refreshError}</p>
      )}
      <ul className="space-y-3 text-sm">
        {assets.map((asset) => (
          <li key={asset.id} className="rounded-lg border border-slate-800 bg-slate-950/50 p-3">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="font-semibold text-slate-100 truncate">{asset.name}</p>
                <p className="text-xs text-slate-400">{asset.ticker}</p>
                {!hideAmounts && <p className="text-xs text-slate-400 mt-1">{asset.units} units</p>}
              </div>
              {!hideAmounts && (
                <div className="text-right">
                  <p className="text-xs text-slate-400">Avg Price</p>
                  <p className="text-emerald-300 font-mono text-sm">${asset.averagePrice.toFixed(2)}</p>
                </div>
              )}
            </div>

            {!hideAmounts && (
              <div className="mt-3 space-y-1">
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <span className="text-slate-400">Current Price</span>
                  <span className="text-right text-slate-200 font-mono">{formatCurrency(asset.currentPrice)}</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <span className="text-slate-400">P/L (price)</span>
                  <span className="text-right text-slate-200 font-mono">
                    {formatCurrency(asset.plValue)} ({formatPercent(asset.plPercent)})
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <span className="text-slate-400">Dividends</span>
                  <span className="text-right text-slate-200 font-mono">{formatCurrency(asset.dividends)}</span>
                </div>

                <div
                  className={`mt-2 rounded-md px-2 py-1 text-xs font-mono text-right ${
                    asset.totalReturnValue === null
                      ? "bg-slate-800/60 text-slate-300"
                      : asset.totalReturnValue > 0
                        ? "bg-emerald-900/50 text-emerald-200"
                        : asset.totalReturnValue < 0
                          ? "bg-rose-900/50 text-rose-200"
                          : "bg-slate-800/60 text-slate-300"
                  }`}
                >
                  Total: {formatCurrency(asset.totalReturnValue)} ({formatPercent(asset.totalReturnPercent)})
                </div>

                <div className="flex items-center justify-between gap-2 text-[11px] text-slate-400 pt-1">
                  <span>{formatFetchedAt(asset.priceFetchedAt)}</span>
                  {asset.isStale && <span className="rounded bg-amber-900/40 px-2 py-0.5 text-amber-300">STALE</span>}
                </div>
              </div>
            )}

            {asset.error && (
              <p className="mt-2 text-xs text-rose-300">Analysis data unavailable for this asset.</p>
            )}
          </li>
        ))}
      </ul>
      {hideAmounts && (
        <div className="mt-3 text-xs text-slate-400">
          <a href="/login" className="underline text-slate-200">
            Log in
          </a>{" "}
          to view prices and returns.
        </div>
      )}
    </aside>
  );
}
