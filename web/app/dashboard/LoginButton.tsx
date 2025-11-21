"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import LoginModal from "@/app/components/LoginModal";
import LoginForm from "@/app/(auth)/login/LoginForm";
import { useAuthToken } from "@/app/hooks/useAuthToken";

interface Props {
  initialAuth: boolean;
}

export default function LoginButton({ initialAuth }: Props) {
  const [open, setOpen] = useState(false);
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

  if (isAuthenticated) {
    return (
      <span className="rounded-md border border-emerald-600/60 bg-emerald-900/30 px-4 py-2 text-sm font-semibold text-emerald-200">
        Logged in
      </span>
    );
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="rounded-md border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-semibold text-slate-100 hover:border-slate-600"
      >
        Login
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
