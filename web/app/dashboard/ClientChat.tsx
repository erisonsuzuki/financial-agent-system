"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import ChatInput from "@/app/components/ChatInput";
import ActionLogTable from "@/app/components/ActionLogTable";
import AssetSidebar from "@/app/components/AssetSidebar";
import { useAuthToken } from "@/app/hooks/useAuthToken";
import { useAssetSummaries } from "@/app/hooks/useAssetSummaries";
import type { AssetSummary } from "@/app/hooks/useAssetSummaries";
import type { AgentAction, RouterResponse } from "@/app/types/router";

interface ClientChatProps {
  initialLogs: AgentAction[];
  initialAuth: boolean;
}

export default function ClientChat({ initialLogs, initialAuth }: ClientChatProps) {
  const isAuthenticated = useAuthToken(initialAuth);
  const queryClient = useQueryClient();
  const { data: assets, isLoading: assetsLoading, error: assetsError } = useAssetSummaries(isAuthenticated);
  const [logs, setLogs] = useState<AgentAction[]>(initialLogs);
  const [refreshingPrices, setRefreshingPrices] = useState(false);
  const [refreshPricesError, setRefreshPricesError] = useState<string | null>(null);
  const mutation = useMutation<RouterResponse, Error, string>({
    mutationFn: async (question: string) => {
      const res = await fetch("/api/router-query", {
        method: "POST",
        body: JSON.stringify({ question }),
      });
      if (!res.ok) {
        throw new Error(await res.text());
      }
      return res.json();
    },
    onSuccess: (_data, question) => {
      setLogs((prev) => [
        {
          id: Date.now(),
          agent_name: _data.agent,
          question,
          response: _data.answer,
          tool_calls: _data.routing_metadata ?? undefined,
          created_at: new Date().toISOString(),
        },
        ...prev,
      ]);
    },
  });

  const handleSubmit = (value: string) => {
    if (!isAuthenticated) return;
    mutation.mutate(value);
  };

  const handleRefreshPrices = async () => {
    if (!isAuthenticated || refreshingPrices) {
      return;
    }

    setRefreshPricesError(null);
    setRefreshingPrices(true);

    try {
      const res = await fetch("/api/assets-summary?refresh=true", {
        cache: "no-store",
        credentials: "include",
      });

      if (res.status === 401) {
        throw new Error("Session expired");
      }

      if (!res.ok) {
        throw new Error("Unable to refresh prices");
      }

      const refreshedAssets = (await res.json()) as AssetSummary[];
      queryClient.setQueryData(["assets-summary", isAuthenticated ? "auth" : "guest", "default"], refreshedAssets);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to refresh prices";
      setRefreshPricesError(message);
      if (message === "Session expired") {
        queryClient.invalidateQueries({ queryKey: ["assets-summary"] });
      }
    } finally {
      setRefreshingPrices(false);
    }
  };

  return (
    <section className="grid gap-6">
      <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(260px,1fr)] lg:items-start">
        <ChatInput onSubmit={handleSubmit} loading={mutation.isPending} isDisabled={!isAuthenticated} />
        <AssetSidebar
          assets={assets}
          loading={assetsLoading}
          error={assetsError ?? null}
          hideAmounts={!isAuthenticated}
          onRefresh={handleRefreshPrices}
          refreshing={refreshingPrices}
          refreshError={refreshPricesError}
        />
      </div>
      {mutation.error && <p className="text-sm text-rose-400">{mutation.error.message}</p>}
      <ActionLogTable entries={logs} />
    </section>
  );
}
