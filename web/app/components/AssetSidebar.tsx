"use client";

import type { AssetSummary } from "@/app/hooks/useAssetSummaries";

interface Props {
  assets: AssetSummary[] | undefined;
  loading: boolean;
  error: Error | null;
}

export default function AssetSidebar({ assets, loading, error }: Props) {
  if (loading) {
    return <div className="rounded-xl border border-slate-800 p-4 text-sm text-slate-400">Loading assets…</div>;
  }
  if (error?.message === "Session expired") {
    return (
      <div className="rounded-xl border border-slate-800 p-4 text-sm text-rose-400">
        Session expired. Please{" "}
        <a href="/auth/login" className="underline text-rose-200">
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
      <header className="flex items-center justify-between text-xs uppercase text-slate-400 mb-3">
        <span>Asset</span>
        <span>Avg Price</span>
      </header>
      <ul className="space-y-2 text-sm">
        {assets.map((asset) => (
          <li key={asset.id} className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="font-semibold text-slate-100 truncate">{asset.name}</p>
              <p className="text-xs text-slate-400">{asset.units} units</p>
            </div>
            <p className="text-emerald-300 font-mono text-sm">${asset.averagePrice.toFixed(2)}</p>
          </li>
        ))}
      </ul>
    </aside>
  );
}
