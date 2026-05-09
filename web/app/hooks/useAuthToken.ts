"use client";

import { useEffect, useState } from "react";

// Detect session status by asking the server (which can read the HTTP-only cookie).
export function useAuthToken(initialAuth = false): boolean {
  const [hasToken, setHasToken] = useState<boolean>(initialAuth);

  useEffect(() => {
    let active = true;
    const retryTimers: ReturnType<typeof setTimeout>[] = [];

    const checkSession = async () => {
      try {
        const res = await fetch("/api/auth/session", { cache: "no-store", credentials: "include" });
        const data = await res.json();
        if (!res.ok) {
          if (active && res.status === 401) {
            setHasToken(false);
          }
          return;
        }
        if (active) setHasToken(Boolean(data.authenticated));
      } catch {
        return;
      }
    };

    checkSession();
    const handleAuthChange = () => {
      // Optimistically mark as authenticated, then verify with the server.
      setHasToken(true);
      checkSession();
      retryTimers.push(setTimeout(() => void checkSession(), 200));
      retryTimers.push(setTimeout(() => void checkSession(), 600));
    };
    const handleFocus = () => checkSession();

    window.addEventListener("fas-auth-changed", handleAuthChange as EventListener);
    window.addEventListener("focus", handleFocus);

    return () => {
      active = false;
      retryTimers.forEach((timer) => clearTimeout(timer));
      window.removeEventListener("fas-auth-changed", handleAuthChange as EventListener);
      window.removeEventListener("focus", handleFocus);
    };
  }, []);

  useEffect(() => {
    setHasToken(initialAuth);
  }, [initialAuth]);

  return hasToken;
}
