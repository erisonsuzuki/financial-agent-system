"use client";

import { useState, type ReactNode } from "react";
import Image from "next/image";
import LoginButton from "./LoginButton";

interface Props {
  initialAuth: boolean;
}

export default function DashboardNavigation({ initialAuth }: Props) {
  const [isCollapsed, setIsCollapsed] = useState(true);

  return (
    <aside
      className={`border-outline-variant bg-surface-lowest flex border-b transition-[width] duration-200 lg:sticky lg:top-0 lg:h-screen lg:shrink-0 lg:flex-col lg:border-b-0 lg:border-r ${isCollapsed ? "lg:w-16" : "lg:w-64"}`}
      onMouseEnter={() => setIsCollapsed(false)}
      onMouseLeave={() => setIsCollapsed(true)}
      onFocusCapture={() => setIsCollapsed(false)}
    >
      <div className="flex justify-center px-3 py-4 lg:py-6">
        <Image src="/brand/logo.png" alt="Financial Agent System" width={96} height={96} className={`rounded-lg object-cover transition-[width,height] duration-200 ${isCollapsed ? "h-10 w-10" : "h-24 w-24"}`} priority />
      </div>
      <nav aria-label="Dashboard" className={`hidden flex-1 lg:block ${isCollapsed ? "px-2" : "px-3"}`}>
        <MenuItem label="Chat" active isCollapsed={isCollapsed} icon={<ChatIcon />} />
        <MenuItem label="Portfolio" isCollapsed={isCollapsed} icon={<PortfolioIcon />} />
      </nav>
      <div className={`ml-auto p-3 lg:ml-0 lg:mt-auto ${isCollapsed ? "lg:p-3" : "lg:p-6"}`}>
        <LoginButton initialAuth={initialAuth} compact={isCollapsed} />
      </div>
    </aside>
  );
}

function MenuItem({ label, active = false, isCollapsed, icon }: { label: string; active?: boolean; isCollapsed: boolean; icon: ReactNode }) {
  return (
    <button type="button" aria-label={label} title={isCollapsed ? label : undefined} className={`mt-2 flex h-12 w-full items-center rounded-lg font-mono text-xs font-semibold tracking-widest ${active ? "bg-neon/10 text-neon" : "text-on-surface-variant hover:bg-surface-high hover:text-on-surface"} ${isCollapsed ? "justify-center" : "gap-4 px-4"}`}>
      {icon}
      {!isCollapsed && label.toUpperCase()}
    </button>
  );
}

function ChatIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="h-4 w-4 shrink-0 fill-none stroke-current stroke-2">
      <path d="M4 4h16v13H9l-5 3V4Z" />
      <path d="M7 8h10M7 12h10" />
    </svg>
  );
}

function PortfolioIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="h-4 w-4 shrink-0 fill-none stroke-current stroke-2">
      <rect x="4" y="5" width="13" height="13" rx="1" />
      <rect x="8" y="8" width="12" height="12" rx="1" />
      <path d="M12 12h4v4h-4z" />
    </svg>
  );
}
