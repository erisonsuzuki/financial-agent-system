"use client";

import { ReactNode } from "react";

interface Props {
  onClose: () => void;
  children: ReactNode;
}

export default function LoginModal({ onClose, children }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="relative w-full max-w-md rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-3 top-3 text-slate-400 hover:text-slate-200"
          aria-label="Close login modal"
        >
          ✕
        </button>
        {children}
      </div>
    </div>
  );
}
