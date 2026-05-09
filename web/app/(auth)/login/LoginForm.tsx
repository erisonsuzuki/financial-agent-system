"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

interface Props {
  onSuccess?: () => void | Promise<void>;
}

type SignInMode = "password" | "magic";

export default function LoginForm({ onSuccess }: Props) {
  const router = useRouter();
  const [mode, setMode] = useState<SignInMode>("magic");
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
      const endpoint = mode === "password" ? "/api/auth/login" : "/api/auth/register";
      const body =
        mode === "password"
          ? {
              email: formData.get("email"),
              password: formData.get("password"),
            }
          : {
              email: formData.get("email"),
            };

      const res = await fetch(endpoint, {
        method: "POST",
        credentials: "include",
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const message = await res.text();
        throw new Error(message || "Unable to sign in");
      }

      const data = await res.json();
      if (mode === "magic") {
        setSuccessMessage(data.message || "Check your email for a magic link.");
      } else if (onSuccess) {
        await onSuccess();
      } else {
        router.push("/dashboard");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div className="grid grid-cols-2 gap-2 rounded-md border border-slate-700 bg-slate-900 p-1">
        <button
          type="button"
          onClick={() => {
            setMode("magic");
            setError(null);
            setSuccessMessage(null);
          }}
          className={`rounded-md px-3 py-2 text-sm font-medium transition ${
            mode === "magic" ? "bg-sky-500 text-white" : "text-slate-300 hover:bg-slate-800"
          }`}
        >
          Magic Link
        </button>
        <button
          type="button"
          onClick={() => {
            setMode("password");
            setError(null);
            setSuccessMessage(null);
          }}
          className={`rounded-md px-3 py-2 text-sm font-medium transition ${
            mode === "password" ? "bg-sky-500 text-white" : "text-slate-300 hover:bg-slate-800"
          }`}
        >
          Email + Password
        </button>
      </div>
      <div>
        <label className="block text-sm font-medium mb-1">Email</label>
        <input
          type="email"
          name="email"
          className="w-full rounded-md border border-slate-600 bg-slate-900 px-3 py-2"
          required
        />
      </div>
      {mode === "password" && (
        <div>
          <label className="block text-sm font-medium mb-1">Password</label>
          <input
            type="password"
            name="password"
            className="w-full rounded-md border border-slate-600 bg-slate-900 px-3 py-2"
            required
          />
        </div>
      )}
      {error && <p className="text-sm text-rose-400">{error}</p>}
      {successMessage && <p className="text-sm text-emerald-400">{successMessage}</p>}
      <button
        type="submit"
        className="w-full rounded-md bg-sky-500 py-2 font-semibold text-white hover:bg-sky-400 disabled:opacity-50"
        disabled={loading}
      >
        {loading ? "Please wait..." : mode === "magic" ? "Send magic link" : "Sign in"}
      </button>
    </form>
  );
}
