"use client";

import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
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

  useEffect(() => {
    if (!isAuthenticated) {
      setLogs([]);
      return;
    }

    const loadLogs = async () => {
      try {
        const res = await fetch("/api/agent-actions", {
          cache: "no-store",
          credentials: "include",
        });
        if (!res.ok) {
          return;
        }
        const data = (await res.json()) as AgentAction[];
        setLogs(data);
      } catch {
        return;
      }
    };

    void loadLogs();
  }, [isAuthenticated]);

  return (
    <section className="min-w-0 flex-1 lg:flex lg:min-h-screen">
      <div className="min-w-0 flex-1 space-y-6 p-4 sm:p-6">
        <header className="max-w-3xl">
          <h1 className="text-2xl font-semibold text-on-surface">Financial Agent System</h1>
          <p className="text-base leading-7 text-on-surface-variant">
            Your financial operations, managed by dedicated agents.
          </p>
        </header>
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
      <ActionLogTable
        entries={logs}
        onSubmit={handleSubmit}
        loading={mutation.isPending}
        isDisabled={!isAuthenticated}
        error={mutation.error}
      />
    </section>
  );
}
