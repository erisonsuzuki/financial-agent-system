"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function CreatePasswordPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setLoading(true);

    const formData = new FormData(event.currentTarget);
    const password = String(formData.get("password") || "");
    const confirmPassword = String(formData.get("confirmPassword") || "");
    if (password !== confirmPassword) {
      setLoading(false);
      setError("Passwords do not match.");
      return;
    }

    try {
      const res = await fetch("/api/auth/magic-link/set-password", {
        method: "POST",
        credentials: "include",
        body: JSON.stringify({ password }),
      });

      if (!res.ok) {
        const message = await res.text();
        throw new Error(message || "Unable to set password.");
      }

      if (typeof window !== "undefined") {
        window.dispatchEvent(new Event("fas-auth-changed"));
      }
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to set password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-24">
      <div className="card">
        <h1 className="text-2xl font-semibold mb-6">Create your password</h1>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
              type="password"
              name="password"
              className="w-full rounded-md border border-slate-600 bg-slate-900 px-3 py-2"
              required
              minLength={8}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Confirm password</label>
            <input
              type="password"
              name="confirmPassword"
              className="w-full rounded-md border border-slate-600 bg-slate-900 px-3 py-2"
              required
              minLength={8}
            />
          </div>
          {error && <p className="text-sm text-rose-400">{error}</p>}
          <button
            type="submit"
            className="w-full rounded-md bg-sky-500 py-2 font-semibold text-white hover:bg-sky-400 disabled:opacity-50"
            disabled={loading}
          >
            {loading ? "Saving..." : "Create password"}
          </button>
        </form>
      </div>
    </div>
  );
}
