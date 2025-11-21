# Implementation Blueprint: Phase16 Assets List (run codex resume 019a8e3a-866d-7a03-a05a-7fec1ac166de)

## Overview
Add an authenticated asset-summary API route plus a React Query hook so the UI can display the user’s holdings (units + average price) beside the chat input, and tighten the action log table column sizing so long questions stay within their column. Work touches the Next.js route handlers, shared hooks, `web/app/dashboard/ClientChat.tsx`, and `ActionLogTable.tsx`. Assumption: single-user environment; per-user ownership/migrations are deferred and noted in “Notes” for future multi-user support.

## Implementation Phases

### Phase 1: Server Asset Summary API + React Query Hook
**Objective**: Reuse the FastAPI `/assets/` and `/assets/{ticker}/analysis` endpoints inside a Next.js route (`/api/assets-summary`) so client components can read normalized asset summaries through React Query without exposing credentials.
**Code Proposal**:
```typescript
// web/app/api/assets-summary/route.ts
import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { fastapiFetch } from "@/app/lib/fas-api";

type Asset = { id: number; ticker: string; name: string };
type AssetAnalysis = { total_quantity: number; average_price: string };

export async function GET(_request: NextRequest) {
  const token = (await cookies()).get("fas_token")?.value;
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const assets = await fastapiFetch<Asset[]>("/assets/", {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!assets.length) {
    return NextResponse.json([]);
  }

  // Batch analysis calls to avoid hammering FastAPI; reuse results via Promise.allSettled
  const enriched = await Promise.all(
    assets.map(async (asset) => {
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
}

// web/app/hooks/useAssetSummaries.ts
import { useQuery } from "@tanstack/react-query";
export function useAssetSummaries() {
  return useQuery({
    queryKey: ["assets-summary"],
    queryFn: async () => {
      const res = await fetch("/api/assets-summary");
      if (res.status === 401) throw new Error("Session expired");
      if (!res.ok) throw new Error("Unable to load assets");
      return res.json() as Promise<AssetSummary[]>;
    },
    staleTime: 60_000,
    gcTime: 5 * 60_000,
  });
}
```
**Tests**:
- Unit test the route handler with mocked `fastapiFetch` to verify it calls the analysis endpoint per ticker, handles unauthorized errors, and returns normalized numeric values.
- Hook test (React Testing Library) that mocks `fetch` to ensure `useAssetSummaries` exposes loading/error states expected by the UI.

### Phase 2: Chat Layout With Asset Sidebar
**Objective**: Update `web/app/dashboard/ClientChat.tsx` (and optionally a small `AssetSidebar` component) to render the chat input and the asset list in a responsive grid so the list floats to the right on desktop and collapses/stacks above on smaller breakpoints.
**Code Proposal**:
```tsx
// web/app/dashboard/ClientChat.tsx
import AssetSidebar from "@/app/components/AssetSidebar";
import { useAssetSummaries } from "@/app/hooks/useAssetSummaries";

export default function ClientChat({ initialLogs }: ClientChatProps) {
  const { data: assets, isLoading, error } = useAssetSummaries();
  ...
  return (
    <section className="grid gap-6">
      <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(260px,1fr)] lg:items-start">
        <ChatInput ... />
        <AssetSidebar assets={assets} loading={isLoading} error={error} />
      </div>
      {mutation.error && ...}
      <ActionLogTable entries={logs} />
    </section>
  );
}

// web/app/components/AssetSidebar.tsx
export function AssetSidebar({ assets, loading, error }: Props) {
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
        {assets?.map((asset) => (
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
```
**Tests**:
- Cypress/Playwright smoke test to confirm the sidebar renders next to the form on desktop and stacks on <1024px viewports.
- Component test verifying empty state (“No assets yet”) renders when the hook returns an empty array.

### Phase 3: Question Column Width & Wrapping
**Objective**: Update `web/app/components/ActionLogTable.tsx` to enforce max-widths and word breaking so the “Question” column honors its layout regardless of message length.
**Code Proposal**:
```tsx
// web/app/components/ActionLogTable.tsx
<td className="px-4 py-3 max-w-xs text-slate-200">
  <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">{entry.question}</p>
  {entry.tool_calls && (
    <pre className="mt-2 rounded bg-slate-950 p-2 text-xs text-slate-400 overflow-x-auto">
      {JSON.stringify(entry.tool_calls, null, 2)}
    </pre>
  )}
</td>
```
Pair this with responsive table container tweaks (`table-fixed`, `w-full`) so the browser respects column widths and long content wraps instead of pushing widths.
**Tests**:
- Storybook screenshot or Jest DOM test ensuring a long string wraps across multiple lines without expanding the table width.
- Manual regression QA on `ActionLogTable` to ensure tool call JSON still scrolls horizontally without shifting layout.

## Consolidated Checklist
- [x] Implement `/api/assets-summary` plus the `useAssetSummaries` React Query hook powered by FastAPI data.
- [x] Render the asset sidebar beside `ChatInput` inside `ClientChat`, covering loading/empty states and responsive stacking.
- [x] Update `ActionLogTable` column classes (max-width + `break-words`) so long questions and responses respect the table layout.

## Notes
- The FastAPI backend already exposes `/assets/` and per-ticker analysis; the new route merely stitches those responses together per authenticated user.
- Keep styling in Tailwind utility classes to match the rest of the repo; the card/border tokens already exist in `ChatInput` and `ActionLogTable`.
- Coordinate with UX on the final desktop vs. mobile stacking breakpoints; defaulting to `lg:` keeps parity with the existing dashboard container widths.
- If the per-ticker analysis fetch becomes slow, plan a FastAPI aggregation endpoint (e.g., `/portfolio/summary`) to batch calculations server-side and drastically reduce round trips; you can also memoize the `/api/assets-summary` response with tag-based revalidation to avoid duplicate work within the cache window.
- Single-user assumption: backend `/assets/` is effectively global; if multi-user is added later, add ownership fields + Alembic migration, scope queries, and update `register_asset_position` to send Authorization headers.
- Document how `register_asset_position` obtains credentials (e.g., orchestrator-supplied JWT or internal API token) if/when auth is enforced on asset endpoints.
