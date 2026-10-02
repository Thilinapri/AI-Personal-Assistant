"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Brain,
  Search,
  Bell,
  History,
  Sparkles,
  X,
  ShieldCheck,
  Activity,
} from "lucide-react";

interface NavItem {
  name: string;
  description: string;
  href: string;
  icon: React.ElementType;
}

const navItems: NavItem[] = [
  {
    name: "Dashboard",
    description: "Overview",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "Memories",
    description: "Saved information",
    href: "/memories",
    icon: Brain,
  },
  {
    name: "Find a Memory",
    description: "Semantic retrieval",
    href: "/search",
    icon: Search,
  },
  {
    name: "Reminders",
    description: "Scheduled alerts",
    href: "/reminders",
    icon: Bell,
  },
  {
    name: "Memory History",
    description: "Previous versions",
    href: "/history",
    icon: History,
  },
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<
  SidebarProps
> = ({
  isOpen,
  onClose,
}) => {
  const pathname = usePathname();

  return (
    <>
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-slate-950/45 backdrop-blur-sm lg:hidden"
          aria-hidden="true"
        />
      )}

      <aside
        className={`fixed bottom-0 left-0 top-0 z-50 flex w-[272px] flex-col overflow-hidden border-r border-slate-800/80 bg-slate-950 text-slate-100 shadow-2xl transition-transform duration-300 ease-out lg:translate-x-0 ${
          isOpen
            ? "translate-x-0"
            : "-translate-x-full"
        }`}
      >
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(99,102,241,0.22),transparent_18rem)]" />

        <div className="relative flex h-[76px] items-center justify-between border-b border-white/10 px-5">
          <Link
            href="/dashboard"
            onClick={onClose}
            className="flex min-w-0 items-center gap-3"
          >
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-lg shadow-indigo-950/40">
              <Sparkles className="h-5 w-5" />
            </div>

            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="truncate text-lg font-bold tracking-tight text-white">
                  EchoMind
                </span>

                <span className="rounded-full border border-indigo-400/20 bg-indigo-400/10 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider text-indigo-300">
                  AI
                </span>
              </div>

              <p className="truncate text-[11px] text-slate-400">
                Personal Memory Assistant
              </p>
            </div>
          </Link>

          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-9 w-9 items-center justify-center rounded-xl text-slate-400 transition hover:bg-white/10 hover:text-white lg:hidden"
            aria-label="Close sidebar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="relative flex-1 overflow-y-auto px-3 py-5">
          <p className="mb-2 px-3 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">
            Workspace
          </p>

          <nav className="space-y-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;

              const isActive =
                pathname === item.href ||
                pathname?.startsWith(
                  `${item.href}/`
                );

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onClose}
                  className={`group flex items-center gap-3 rounded-2xl px-3 py-3 transition-all ${
                    isActive
                      ? "bg-white text-slate-950 shadow-lg shadow-black/20"
                      : "text-slate-300 hover:bg-white/8 hover:text-white"
                  }`}
                >
                  <div
                    className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl transition-all ${
                      isActive
                        ? "bg-indigo-100 text-indigo-700"
                        : "bg-white/5 text-slate-400 group-hover:bg-white/10 group-hover:text-indigo-300"
                    }`}
                  >
                    <Icon className="h-[17px] w-[17px]" />
                  </div>

                  <div className="min-w-0 flex-1">
                    <p
                      className={`truncate text-sm font-semibold ${
                        isActive
                          ? "text-slate-950"
                          : "text-inherit"
                      }`}
                    >
                      {item.name}
                    </p>

                    <p
                      className={`truncate text-[10px] ${
                        isActive
                          ? "text-slate-500"
                          : "text-slate-500"
                      }`}
                    >
                      {item.description}
                    </p>
                  </div>

                  {isActive && (
                    <span className="h-2 w-2 rounded-full bg-indigo-500" />
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="relative border-t border-white/10 p-4">
          <div className="rounded-2xl border border-white/10 bg-white/[0.045] p-4">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-200">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-400/10 text-emerald-300">
                <Activity className="h-3.5 w-3.5" />
              </div>

              EchoMind System
            </div>

            <p className="mt-2 text-[10px] leading-relaxed text-slate-400">
              Memories, retrieval and smart reminders in one workspace.
            </p>

            <div className="mt-3 flex items-center gap-1.5 text-[10px] font-medium text-emerald-300">
              <ShieldCheck className="h-3 w-3" />
              Local-first memory storage
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};