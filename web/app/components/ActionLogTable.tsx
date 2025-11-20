import type { AgentAction } from "@/app/types/router";

interface Props {
  entries: AgentAction[];
}

export default function ActionLogTable({ entries }: Props) {
  if (!entries.length) {
    return <p className="text-slate-400">No actions logged yet.</p>;
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-800">
      <table className="min-w-full table-fixed text-sm">
        <thead className="bg-slate-900 text-left uppercase text-slate-400">
          <tr>
            <th className="px-4 py-3 w-40">Timestamp</th>
            <th className="px-4 py-3 w-32">Agent</th>
            <th className="px-4 py-3 w-80">Question</th>
            <th className="px-4 py-3">Response</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {entries.map((entry) => (
            <tr key={`${entry.id}-${entry.created_at}`} className="align-top">
              <td className="px-4 py-3 text-slate-400">
                {new Date(entry.created_at).toLocaleString()}
              </td>
              <td className="px-4 py-3 font-semibold text-sky-300 break-words">{entry.agent_name}</td>
              <td className="px-4 py-3 text-slate-200 max-w-xs">
                <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">{entry.question}</p>
                {entry.tool_calls && (
                  <pre className="mt-2 rounded bg-slate-950 p-2 text-xs text-slate-400 overflow-x-auto">
{JSON.stringify(entry.tool_calls, null, 2)}
                  </pre>
                )}
              </td>
              <td className="px-4 py-3 text-slate-200 max-w-sm">
                <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">{entry.response}</p>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
