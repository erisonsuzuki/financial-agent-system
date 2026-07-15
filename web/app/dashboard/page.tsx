import { readAuthCookie } from "@/app/lib/auth";
import { fastapiFetch } from "@/app/lib/fas-api";
import ClientChat from "./ClientChat";
import type { AgentAction } from "@/app/types/router";
import DashboardNavigation from "./DashboardNavigation";

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
    <main className="min-h-screen bg-surface lg:flex">
      <DashboardNavigation initialAuth={Boolean(token)} />
      <ClientChat initialLogs={logs} initialAuth={Boolean(token)} />
    </main>
  );
}
