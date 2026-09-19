"use client";

import React, { useState } from "react";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";

interface ShellProps {
  children: React.ReactNode;
}

export const Shell: React.FC<ShellProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* Sidebar Navigation */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main content column with offset for desktop sidebar */}
      <div className="flex min-h-screen flex-col lg:pl-64">
        <Header onMenuToggle={() => setSidebarOpen((prev) => !prev)} />

        <main className="flex-1 px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
          <div className="mx-auto max-w-6xl">{children}</div>
        </main>

        <footer className="border-t border-slate-200 bg-white px-4 py-4 sm:px-6 lg:px-8">
          <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 text-xs text-slate-500 sm:flex-row">
            <span>EchoMind AI Personal Memory Assistant &copy; 2026</span>
            <span>Next.js App Router Shell • University Project</span>
          </div>
        </footer>
      </div>
    </div>
  );
};
