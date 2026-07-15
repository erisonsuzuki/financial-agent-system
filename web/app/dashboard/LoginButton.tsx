"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import LoginModal from "@/app/components/LoginModal";
import LoginForm from "@/app/(auth)/login/LoginForm";
import { useAuthToken } from "@/app/hooks/useAuthToken";

interface Props {
  initialAuth: boolean;
  compact?: boolean;
}

export default function LoginButton({ initialAuth, compact = false }: Props) {
  const [open, setOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const [logoutError, setLogoutError] = useState<string | null>(null);
  const isAuthenticated = useAuthToken(initialAuth);
  const queryClient = useQueryClient();
  const router = useRouter();

  const handleSuccess = async () => {
    setOpen(false);
    await queryClient.invalidateQueries({ predicate: (q) => Array.isArray(q.queryKey) && q.queryKey[0] === "assets-summary" });
    await queryClient.refetchQueries({ predicate: (q) => Array.isArray(q.queryKey) && q.queryKey[0] === "assets-summary" });
    await queryClient.invalidateQueries({ predicate: (q) => Array.isArray(q.queryKey) && q.queryKey[0] === "agent-actions" });
    await queryClient.refetchQueries({ predicate: (q) => Array.isArray(q.queryKey) && q.queryKey[0] === "agent-actions" });
    router.refresh();
  };

  const handleLogout = async () => {
    setLogoutError(null);
    setLoggingOut(true);

    try {
      const response = await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
      if (!response.ok) {
        throw new Error("Unable to log out");
      }
      queryClient.clear();
      router.refresh();
    } catch (error) {
      setLogoutError(error instanceof Error ? error.message : "Unable to log out");
    } finally {
      setLoggingOut(false);
    }
  };

  if (isAuthenticated) {
    return (
      <div>
        <button
          type="button"
          onClick={handleLogout}
          disabled={loggingOut}
          aria-label={compact ? "Log out" : undefined}
          title={compact ? "Log out" : undefined}
          className={`flex items-center gap-4 rounded-lg font-mono text-xs font-semibold tracking-widest text-[#bfc6dc] transition hover:bg-surface-high hover:text-on-surface disabled:cursor-not-allowed disabled:opacity-50 ${compact ? "h-10 w-10 justify-center" : "h-12 px-3"}`}
        >
          <LogoutIcon />
          {!compact && (loggingOut ? "LOGGING OUT..." : "LOGOUT")}
        </button>
        {logoutError && <p className="mt-2 text-xs text-error">{logoutError}</p>}
      </div>
    );
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label={compact ? "Log in" : undefined}
        className={`rounded-md border border-outline-variant bg-surface-container font-mono text-xs font-semibold tracking-wide text-on-surface hover:border-neon ${compact ? "flex h-10 w-10 items-center justify-center" : "px-4 py-2"}`}
      >
        {compact ? <LoginIcon /> : "Login"}
      </button>
      {open && (
        <LoginModal onClose={() => setOpen(false)}>
          <h2 className="text-xl font-semibold mb-4">Sign in</h2>
          <LoginForm onSuccess={handleSuccess} />
        </LoginModal>
      )}
    </>
  );
}

function LoginIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="h-4 w-4 fill-none stroke-current stroke-2">
      <path d="M14 5h5v14h-5M10 8l4 4-4 4M14 12H5" />
    </svg>
  );
}

function LogoutIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="h-6 w-6 shrink-0 fill-none stroke-current stroke-2">
      <path d="M10 5H5v14h5M14 8l4 4-4 4M10 12h9" />
    </svg>
  );
}
