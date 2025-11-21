"use client";

import { useEffect, useState } from "react";

// Detect session status by asking the server (which can read the HTTP-only cookie).
export function useAuthToken(initialAuth = false): boolean {
  const [hasToken, setHasToken] = useState<boolean>(initialAuth);

  useEffect(() => {
    let active = true;

    const checkSession = async () => {
      try {
        const res = await fetch("/api/auth/session", { cache: "no-store", credentials: "include" });
        const data = await res.json();
        if (!res.ok) {
          if (active) setHasToken(false);
          return;
        }
        if (active) setHasToken(Boolean(data.authenticated));
      } catch (err) {
        if (active) setHasToken(false);
      }
    };

    checkSession();
    const handleAuthChange = () => {
      // Optimistically mark as authenticated, then verify with the server.
      setHasToken(true);
      checkSession();
    };
    const handleFocus = () => checkSession();

    window.addEventListener("fas-auth-changed", handleAuthChange as EventListener);
    window.addEventListener("focus", handleFocus);

    return () => {
      active = false;
      window.removeEventListener("fas-auth-changed", handleAuthChange as EventListener);
      window.removeEventListener("focus", handleFocus);
    };
  }, []);

  return hasToken;
}
