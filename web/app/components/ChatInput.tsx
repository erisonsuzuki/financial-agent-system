"use client";

import { useState } from "react";

interface ChatInputProps {
  onSubmit: (value: string) => void;
  loading?: boolean;
}

export default function ChatInput({ onSubmit, loading }: ChatInputProps) {
  const [question, setQuestion] = useState("");

  return (
    <form
      className="rounded-xl border border-slate-700 bg-slate-900 p-4"
      onSubmit={(event) => {
        event.preventDefault();
        if (!question.trim()) return;
        onSubmit(question.trim());
        setQuestion("");
      }}
    >
      <label className="block text-sm font-semibold mb-2 text-slate-300">
        Ask a question
      </label>
      <textarea
        className="w-full resize-none rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
        rows={4}
        placeholder="e.g. Register 50 shares of ITSA4 at R$10"
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
      />
      <div className="mt-3 flex items-center justify-between">
        <p className="text-xs text-slate-500">Router auto-selects registration/management/analysis agents.</p>
        <button
          type="submit"
          disabled={loading}
          className="rounded-md bg-emerald-500 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-400 disabled:opacity-50"
        >
          {loading ? "Sending..." : "Send"}
        </button>
      </div>
    </form>
  );
}
