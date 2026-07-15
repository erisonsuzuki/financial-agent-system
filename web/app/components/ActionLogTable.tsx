"use client";

import { useEffect, useRef } from "react";
import type { AgentAction } from "@/app/types/router";
import { formatUtcTimestamp } from "@/app/lib/datetime";
import ChatInput from "./ChatInput";

interface Props {
  entries: AgentAction[];
  onSubmit: (value: string) => void;
  loading: boolean;
  isDisabled: boolean;
  error: Error | null;
}

export default function ActionLogTable({ entries, onSubmit, loading, isDisabled, error }: Props) {
  const chronologicalEntries = [...entries].reverse();
  const historyRef = useRef<HTMLOListElement>(null);

  useEffect(() => {
    historyRef.current?.scrollTo({ top: historyRef.current.scrollHeight });
  }, [chronologicalEntries.length]);

  return (
    <aside className="border-outline-variant bg-surface-lowest flex h-[min(70vh,600px)] flex-col border-t lg:h-screen lg:min-h-0 lg:w-[420px] lg:shrink-0 lg:border-l lg:border-t-0">
      <ChatHeader />
      {chronologicalEntries.length ? (
        <ol ref={historyRef} className="min-h-0 flex-1 space-y-6 overflow-y-auto p-4" aria-label="Agent chat history">
          {chronologicalEntries.map((entry) => (
          <li key={`${entry.id}-${entry.created_at}`} className="space-y-4">
            <div className="flex flex-col items-end gap-1">
              <p className="max-w-[85%] rounded-xl rounded-tr-none border border-neon/30 bg-surface-high px-4 py-3 text-sm leading-relaxed text-on-surface">{entry.question}</p>
              <time className="font-mono text-[10px] text-on-surface-variant">{formatUtcTimestamp(entry.created_at)}</time>
            </div>
            <div className="flex flex-col items-start gap-1">
              <div className="max-w-[85%] rounded-xl rounded-tl-none border border-outline-variant bg-surface-container px-4 py-3 text-sm text-on-surface">
                <p className="whitespace-pre-wrap break-words leading-relaxed">{entry.response}</p>
                {entry.tool_calls ? (
                  <details className="group mt-3 rounded-lg bg-surface-lowest p-2">
                    <summary className="flex cursor-pointer list-none items-center justify-between font-mono text-[10px] font-semibold tracking-wide text-neon">
                      <span className="flex items-center gap-1.5">
                        <AgentStatusIcon />
                        {entry.agent_name}
                      </span>
                      <span className="flex h-6 w-6 items-center justify-center rounded bg-surface-high">
                        <svg viewBox="0 0 24 24" aria-hidden="true" className="h-4 w-4 fill-none stroke-current stroke-2 transition-transform group-open:rotate-180">
                          <path d="m6 9 6 6 6-6" />
                        </svg>
                      </span>
                    </summary>
                    <JsonMetadata metadata={withoutAgentName(entry.tool_calls)} />
                  </details>
                ) : (
                  <div className="mt-3 border-t border-outline-variant/50 pt-3 font-mono text-[10px] font-semibold tracking-wide text-neon">{entry.agent_name}</div>
                )}
              </div>
              <time className="font-mono text-[10px] text-on-surface-variant">{formatUtcTimestamp(entry.created_at)}</time>
            </div>
          </li>
          ))}
        </ol>
      ) : (
        <p className="m-auto px-6 text-center text-sm text-on-surface-variant">No actions logged yet. Ask the router a question to begin.</p>
      )}
      <footer className="shrink-0 border-t border-outline-variant bg-surface-container p-4">
        {error && <p className="mb-2 rounded border border-error-container bg-error-container/20 px-2 py-1 text-xs text-error">{error.message}</p>}
        <ChatInput onSubmit={onSubmit} loading={loading} isDisabled={isDisabled} compact />
      </footer>
    </aside>
  );
}

function AgentStatusIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="h-4 w-4 shrink-0 fill-none stroke-current stroke-2">
      <path d="m12 2 2.1 2.3 3.1-.2.8 3 2.7 1.6-1.2 2.9 1.2 2.9-2.7 1.6-.8 3-3.1-.2L12 22l-2.1-2.3-3.1.2-.8-3-2.7-1.6 1.2-2.9-1.2-2.9 2.7-1.6.8-3 3.1.2L12 2Z" />
      <path d="m8.5 12 2.2 2.2 4.8-4.8" />
    </svg>
  );
}

function withoutAgentName(metadata: Record<string, unknown>) {
  return Object.fromEntries(
    Object.entries(metadata)
      .filter(([key]) => key !== "agent_name")
      .map(([key, value]) => [key === "executed_tool_names" ? "tools" : key, value]),
  );
}

function JsonMetadata({ metadata }: { metadata: Record<string, unknown> }) {
  return (
    <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap break-words rounded bg-[#070b13] px-3 py-2 font-mono text-[10px] leading-5 text-on-surface-variant">
      <span>{"{"}</span>
      {Object.entries(metadata).map(([key, value], index) => (
        <span key={key} className="block pl-2">
          <span className="text-on-surface">&quot;{key}&quot;</span>
          <span className="text-on-surface-variant">: </span>
          <JsonValue value={value} />
          {index < Object.keys(metadata).length - 1 && <span className="text-on-surface-variant">,</span>}
        </span>
      ))}
      <span>{"}"}</span>
    </pre>
  );
}

function JsonValue({ value }: { value: unknown }) {
  if (typeof value === "string") {
    return <span className="text-neon">&quot;{value}&quot;</span>;
  }
  if (typeof value === "number") {
    return <span className="text-neon">{value}</span>;
  }
  if (typeof value === "boolean" || value === null) {
    return <span className="text-error">{String(value)}</span>;
  }

  return <span className="text-neon">{JSON.stringify(value)}</span>;
}

function ChatHeader() {
  return (
    <header className="border-outline-variant flex items-center gap-3 border-b p-4">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-neon font-mono text-lg font-bold text-neon-ink" aria-hidden="true">A</div>
      <div>
        <h2 className="text-lg font-semibold text-white">Chat</h2>
        <p className="font-mono text-[10px] font-semibold tracking-widest text-on-surface-variant"><span className="mr-1 inline-block h-2 w-2 rounded-full bg-neon" />ACTIVE</p>
      </div>
    </header>
  );
}
