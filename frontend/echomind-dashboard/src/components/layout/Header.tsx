"use client";

import React from "react";
import {
  Menu,
  Sparkles,
  CircleUserRound,
} from "lucide-react";

interface HeaderProps {
  onMenuToggle?: () => void;
}

export const Header: React.FC<
  HeaderProps
> = ({
  onMenuToggle,
}) => {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/70 bg-white/75 backdrop-blur-xl">
      <div className="flex h-[76px] w-full items-center justify-between px-4 sm:px-6 lg:px-10">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onMenuToggle}
            className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 shadow-sm transition hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700 lg:hidden"
            aria-label="Toggle navigation menu"
          >
            <Menu className="h-5 w-5" />
          </button>

          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-bold tracking-tight text-slate-950 sm:text-lg">
                EchoMind Workspace
              </span>

              <span className="hidden rounded-full border border-indigo-100 bg-indigo-50 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-indigo-600 sm:inline-flex">
                Live
              </span>
            </div>

            <p className="mt-0.5 text-[11px] font-medium text-slate-500">
              Intelligent memory & reminder dashboard
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <div className="hidden items-center gap-2 rounded-xl border border-slate-200/80 bg-white px-3 py-2 shadow-sm sm:flex">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
              <Sparkles className="h-3.5 w-3.5" />
            </div>

            <div>
              <p className="text-[10px] font-semibold text-slate-700">
                AI Memory Assistant
              </p>

              <p className="text-[9px] text-slate-400">
                EchoMind
              </p>
            </div>
          </div>

          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-500 shadow-sm">
            <CircleUserRound className="h-5 w-5" />
          </div>
        </div>
      </div>
    </header>
  );
};