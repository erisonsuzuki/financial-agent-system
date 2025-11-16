"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import ChatInput from "@/app/components/ChatInput";
import ActionLogTable from "@/app/components/ActionLogTable";
import type { AgentAction, RouterResponse } from "@/app/types/router";

interface ClientChatProps {
  initialLogs: AgentAction[];
}

export default function ClientChat({ initialLogs }: ClientChatProps) {
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

  return (
    <section className="grid gap-6">
      <ChatInput onSubmit={(value) => mutation.mutate(value)} loading={mutation.isPending} />
      {mutation.error && <p className="text-sm text-rose-400">{mutation.error.message}</p>}
      <ActionLogTable entries={logs} />
    </section>
  );
}
