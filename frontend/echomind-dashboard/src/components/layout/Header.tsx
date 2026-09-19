"use client";

import React from "react";
import { Menu, Sparkles } from "lucide-react";

interface HeaderProps {
  onMenuToggle?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onMenuToggle }) => {
  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur-sm sm:px-6 lg:px-8">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenuToggle}
          className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 lg:hidden cursor-pointer"
          aria-label="Toggle navigation menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold tracking-tight text-slate-900">
              EchoMind
            </span>
          </div>
          <span className="text-xs font-medium text-slate-500">
            Your Personal Memory Assistant
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2 text-xs text-slate-500">
        <div className="flex items-center gap-1.5 rounded-full bg-slate-50 border border-slate-200 px-3 py-1 font-medium text-slate-600">
          <Sparkles className="h-3.5 w-3.5 text-indigo-500" />
          <span>Personal Assistant</span>
        </div>
      </div>
    </header>
  );
};
