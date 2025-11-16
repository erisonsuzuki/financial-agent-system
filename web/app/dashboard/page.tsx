import { requireSession } from "@/app/lib/auth";
import { fastapiFetch } from "@/app/lib/fas-api";
import ClientChat from "./ClientChat";
import type { AgentAction } from "@/app/types/router";

export default async function DashboardPage() {
  const session = await requireSession();
  const logs = await fastapiFetch<AgentAction[]>("/agent-actions/", {
    headers: {
      Authorization: `Bearer ${session.token}`,
    },
  }).catch(() => []);

  return (
    <main className="container mx-auto grid gap-6">
      <div>
        <h1 className="text-3xl font-semibold mb-4">Financial Agent Console</h1>
        <p className="text-slate-400 max-w-2xl">
          Ask questions in natural language and the router will select the best agent. Recent actions are listed below with routing metadata.
        </p>
      </div>
      <ClientChat initialLogs={logs} />
    </main>
  );
}
