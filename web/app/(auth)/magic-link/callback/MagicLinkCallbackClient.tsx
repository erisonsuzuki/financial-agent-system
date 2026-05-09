"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function MagicLinkCallbackClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setError("Missing token in link.");
      return;
    }

    const consume = async () => {
      try {
        const res = await fetch("/api/auth/magic-link/consume", {
          method: "POST",
          credentials: "include",
          body: JSON.stringify({ token }),
        });
        if (!res.ok) {
          const message = await res.text();
          throw new Error(message || "Invalid or expired link.");
        }

        const data = await res.json();
        if (data.requires_password_setup) {
          router.replace("/create-password");
          return;
        }

        if (typeof window !== "undefined") {
          window.dispatchEvent(new Event("fas-auth-changed"));
        }
        router.replace("/dashboard");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Invalid or expired link.");
      }
    };

    void consume();
  }, [router, searchParams]);

  return (
    <div className="max-w-md mx-auto mt-24">
      <div className="card">
        <h1 className="text-2xl font-semibold mb-4">Checking your link</h1>
        {error ? <p className="text-sm text-rose-400">{error}</p> : <p className="text-sm text-slate-300">Please wait...</p>}
      </div>
    </div>
  );
}
