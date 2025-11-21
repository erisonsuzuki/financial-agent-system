"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import ChatInput from "@/app/components/ChatInput";
import ActionLogTable from "@/app/components/ActionLogTable";
import AssetSidebar from "@/app/components/AssetSidebar";
import { useAuthToken } from "@/app/hooks/useAuthToken";
import { useAssetSummaries } from "@/app/hooks/useAssetSummaries";
import type { AgentAction, RouterResponse } from "@/app/types/router";

interface ClientChatProps {
  initialLogs: AgentAction[];
  initialAuth: boolean;
}

export default function ClientChat({ initialLogs, initialAuth }: ClientChatProps) {
  const isAuthenticated = useAuthToken(initialAuth);
  const { data: assets, isLoading: assetsLoading, error: assetsError } = useAssetSummaries(isAuthenticated);
  const [logs, setLogs] = useState<AgentAction[]>(initialLogs);
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

  return (
    <section className="grid gap-6">
      <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(260px,1fr)] lg:items-start">
        <ChatInput onSubmit={handleSubmit} loading={mutation.isPending} isDisabled={!isAuthenticated} />
        <AssetSidebar assets={assets} loading={assetsLoading} error={assetsError ?? null} hideAmounts={!isAuthenticated} />
      </div>
      {mutation.error && <p className="text-sm text-rose-400">{mutation.error.message}</p>}
      <ActionLogTable entries={logs} />
    </section>
  );
}
