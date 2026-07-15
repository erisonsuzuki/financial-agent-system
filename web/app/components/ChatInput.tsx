"use client";

import { useState } from "react";

interface ChatInputProps {
  onSubmit: (value: string) => void;
  loading?: boolean;
  isDisabled?: boolean;
  compact?: boolean;
}

export default function ChatInput({ onSubmit, loading, isDisabled = false, compact = false }: ChatInputProps) {
  const [question, setQuestion] = useState("");

  if (compact) {
    return (
      <form
        className="flex items-center gap-2 rounded-full border border-outline-variant bg-surface-lowest px-3 py-2 focus-within:border-neon"
        onSubmit={(event) => {
          event.preventDefault();
          if (isDisabled || !question.trim()) return;
          onSubmit(question.trim());
          setQuestion("");
        }}
      >
        <label htmlFor="chat-message" className="sr-only">Message the agent</label>
        <input
          id="chat-message"
          className="min-w-0 flex-1 bg-transparent px-2 py-1 text-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none disabled:cursor-not-allowed"
          placeholder={isDisabled ? "Log in to ask a question" : "Type a message..."}
          value={question}
          disabled={isDisabled}
          onChange={(event) => setQuestion(event.target.value)}
        />
        <button
          type="submit"
          aria-label="Send message"
          disabled={loading || isDisabled}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-neon font-mono text-sm font-bold text-neon-ink transition hover:bg-neon-dim disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "..." : ">"}
        </button>
      </form>
    );
  }

  return (
    <form
      className="relative overflow-hidden rounded-xl border border-outline-variant bg-surface-container p-4 sm:p-6"
      onSubmit={(event) => {
        event.preventDefault();
        if (isDisabled) return;
        if (!question.trim()) return;
        onSubmit(question.trim());
        setQuestion("");
      }}
    >
      <label htmlFor="agent-question" className="mb-4 block font-mono text-xs font-semibold tracking-widest text-on-surface-variant">
        Ask a question
      </label>
      <textarea
        id="agent-question"
        className="min-h-40 w-full resize-none rounded-lg border border-outline-variant bg-surface-lowest px-4 py-3 font-mono text-base text-on-surface placeholder:text-on-surface-variant/40 focus:border-neon focus:outline-none focus:ring-1 focus:ring-neon disabled:cursor-not-allowed disabled:opacity-50"
        rows={5}
        placeholder="e.g. Register 50 shares of ITSA4 at R$10"
        value={question}
        disabled={isDisabled}
        onChange={(event) => setQuestion(event.target.value)}
      />
      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs italic text-on-surface-variant">Router auto-selects registration/management/analysis agents.</p>
        <button
          type="submit"
          disabled={loading || isDisabled}
          className="rounded-lg bg-neon px-8 py-3 font-mono text-xs font-semibold tracking-widest text-neon-ink transition hover:bg-neon-dim disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isDisabled ? "Login to ask" : loading ? "Sending..." : "Send"}
        </button>
      </div>
    </form>
  );
}
