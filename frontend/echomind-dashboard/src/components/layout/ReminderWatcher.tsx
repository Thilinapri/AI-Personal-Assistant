"use client";

import React, {
  useEffect,
  useRef,
  useState,
} from "react";

import Link from "next/link";

import {
  formatDateTime,
} from "@/lib/formatters";

import {
  ApiRemindersResponse,
  Reminder,
} from "@/types/api";

import {
  BellRing,
  Clock,
  X,
} from "lucide-react";

export const ReminderWatcher = () => {
  const knownTriggeredIds =
    useRef<Set<number>>(new Set());

  const initialized =
    useRef(false);

  const [
    activeReminder,
    setActiveReminder,
  ] = useState<Reminder | null>(null);

  useEffect(() => {
    let cancelled = false;

    const checkReminders =
      async () => {
        try {
          const response =
            await fetch(
              "/api/reminders",
              {
                cache: "no-store",
              },
            );

          const data =
            (await response.json()) as ApiRemindersResponse;

          if (
            cancelled ||
            !data.available ||
            !data.reminders
          ) {
            return;
          }

          const triggered =
            data.reminders.filter(
              (reminder) => {
                const status =
                  reminder.status
                    .trim()
                    .toLowerCase();

                return (
                  status === "triggered" ||
                  status === "notified"
                );
              },
            );

          if (!initialized.current) {
            for (
              const reminder
              of triggered
            ) {
              knownTriggeredIds.current.add(
                reminder.id,
              );
            }

            initialized.current = true;

            return;
          }

          const newlyTriggered =
            triggered.filter(
              (reminder) =>
                !knownTriggeredIds.current.has(
                  reminder.id,
                ),
            );

          for (
            const reminder
            of newlyTriggered
          ) {
            knownTriggeredIds.current.add(
              reminder.id,
            );
          }

          if (
            newlyTriggered.length > 0
          ) {
            const newest =
              [...newlyTriggered].sort(
                (first, second) =>
                  second.id - first.id,
              )[0];

            setActiveReminder(
              newest,
            );
          }
        } catch {
          // Silent while backend is unavailable.
        }
      };

    checkReminders();

    const interval =
      window.setInterval(
        checkReminders,
        5000,
      );

    return () => {
      cancelled = true;

      window.clearInterval(
        interval,
      );
    };
  }, []);

  if (!activeReminder) {
    return null;
  }

  return (
    <div className="fixed right-4 top-24 z-[100] w-[calc(100%-2rem)] max-w-sm sm:right-6">
      <div className="overflow-hidden rounded-2xl border border-indigo-200 bg-white shadow-[0_18px_55px_rgba(15,23,42,0.22)]">
        <div className="bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-3 text-white">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-white/15">
                <BellRing className="h-4 w-4" />
              </div>

              <div>
                <p className="text-xs font-bold">
                  EchoMind Reminder
                </p>

                <p className="text-[10px] text-indigo-100">
                  It&apos;s time for something you asked EchoMind to remember.
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() =>
                setActiveReminder(null)
              }
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-indigo-100 transition hover:bg-white/10 hover:text-white"
              aria-label="Dismiss reminder"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="p-4">
          <h3 className="text-sm font-bold text-slate-950">
            {activeReminder.title}
          </h3>

          <p className="mt-1.5 text-xs leading-relaxed text-slate-600">
            {activeReminder.content}
          </p>

          {activeReminder.reminder_time && (
            <div className="mt-3 flex items-center gap-1.5 text-[10px] font-medium text-slate-500">
              <Clock className="h-3.5 w-3.5" />

              Scheduled for{" "}
              {formatDateTime(
                activeReminder.reminder_time,
              )}
            </div>
          )}

          <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-[10px] font-bold text-emerald-700">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              NOTIFIED
            </span>

            <Link
              href="/reminders"
              onClick={() =>
                setActiveReminder(null)
              }
              className="text-xs font-bold text-indigo-600 transition hover:text-indigo-800"
            >
              View Reminders
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};