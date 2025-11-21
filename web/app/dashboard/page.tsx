import { readAuthCookie } from "@/app/lib/auth";
import { fastapiFetch } from "@/app/lib/fas-api";
import ClientChat from "./ClientChat";
import type { AgentAction } from "@/app/types/router";
import LoginButton from "./LoginButton";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function DashboardPage() {
  const token = await readAuthCookie();
  const logs = token
    ? await fastapiFetch<AgentAction[]>("/agent-actions/", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }).catch(() => [])
    : [];

  return (
    <main className="container mx-auto grid gap-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold mb-4">Financial Agent Console</h1>
          <p className="text-slate-400 max-w-2xl">
            Ask questions in natural language and the router will select the best agent. Recent actions are listed below with routing metadata.
          </p>
        </div>
        <LoginButton initialAuth={Boolean(token)} />
      </div>
      <ClientChat initialLogs={logs} initialAuth={Boolean(token)} />
    </main>
  );
}
