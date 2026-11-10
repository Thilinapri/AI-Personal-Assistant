"use client";

import React, {
  useState,
} from "react";

import {
  Sidebar,
} from "./Sidebar";

import {
  Header,
} from "./Header";

import {
  ReminderWatcher,
} from "./ReminderWatcher";

interface ShellProps {
  children:
    React.ReactNode;
}

export const Shell:
React.FC<ShellProps> = ({
  children,
}) => {
  const [
    sidebarOpen,
    setSidebarOpen,
  ] = useState(false);

  return (
    <div className="min-h-screen text-slate-900">

      <Sidebar
        isOpen={
          sidebarOpen
        }
        onClose={() =>
          setSidebarOpen(
            false,
          )
        }
      />


      <ReminderWatcher />


      <div className="flex min-h-screen flex-col lg:pl-[272px]">

        <Header
          onMenuToggle={() =>
            setSidebarOpen(
              (
                previous,
              ) =>
                !previous,
            )
          }
        />


        <main className="flex-1 px-4 py-6 sm:px-6 sm:py-8 lg:px-10 lg:py-9">

          <div className="mx-auto w-full max-w-[1280px]">
            {children}
          </div>

        </main>


        <footer className="px-4 pb-6 pt-2 sm:px-6 lg:px-10">

          <div className="mx-auto flex max-w-[1280px] items-center justify-between rounded-2xl border border-white/70 bg-white/65 px-4 py-3 text-[11px] text-slate-500 shadow-sm backdrop-blur-xl sm:px-5">

            <span>
              EchoMind — Remember what matters.
            </span>

            <span className="hidden sm:inline">
              AI Personal Memory Assistant · 2026
            </span>

          </div>

        </footer>

      </div>

    </div>
  );
};