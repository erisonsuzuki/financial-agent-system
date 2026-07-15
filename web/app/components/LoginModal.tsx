"use client";

import { ReactNode, useEffect, useRef } from "react";
import { createPortal } from "react-dom";

interface Props {
  onClose: () => void;
  children: ReactNode;
}

export default function LoginModal({ onClose, children }: Props) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const previouslyFocusedRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    previouslyFocusedRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    closeButtonRef.current?.focus();

    return () => previouslyFocusedRef.current?.focus();
  }, []);

  if (typeof document === "undefined") {
    return null;
  }

  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Escape") {
      onClose();
      return;
    }

    if (event.key !== "Tab") return;

    const focusable = dialogRef.current?.querySelectorAll<HTMLElement>(
      'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href]',
    );
    if (!focusable?.length) return;

    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  };

  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 p-4" role="dialog" aria-modal="true" aria-label="Sign in" onKeyDown={handleKeyDown}>
      <div ref={dialogRef} className="relative w-full max-w-md rounded-xl border border-outline-variant bg-surface-container p-6 shadow-xl">
        <button
          ref={closeButtonRef}
          type="button"
          onClick={onClose}
          className="absolute right-3 top-3 text-on-surface-variant hover:text-on-surface"
          aria-label="Close login modal"
        >
          ✕
        </button>
        {children}
      </div>
    </div>,
    document.body,
  );
}
