"use client";

import { useState } from "react";

interface Props {
  onSuccess?: () => void | Promise<void>;
}

export default function LoginForm({ onSuccess: _onSuccess }: Props) {
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSuccessMessage(null);
    setLoading(true);
    const formData = new FormData(event.currentTarget);
    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        credentials: "include",
        body: JSON.stringify({
          email: formData.get("email"),
        }),
      });

      if (!res.ok) {
        const message = await res.text();
        throw new Error(message || "Unable to sign in");
      }

      const data = await res.json();
      setSuccessMessage(data.message || "Check your email for a magic link.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div>
        <label className="block text-sm font-medium mb-1">Email</label>
        <input
          type="email"
          name="email"
          className="w-full rounded-md border border-slate-600 bg-slate-900 px-3 py-2"
          required
        />
      </div>
      {error && <p className="text-sm text-rose-400">{error}</p>}
      {successMessage && <p className="text-sm text-emerald-400">{successMessage}</p>}
      <button
        type="submit"
        className="w-full rounded-md bg-sky-500 py-2 font-semibold text-white hover:bg-sky-400 disabled:opacity-50"
        disabled={loading}
      >
        {loading ? "Sending link..." : "Send magic link"}
      </button>
    </form>
  );
}
