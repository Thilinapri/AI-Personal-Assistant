"use client";

import React, {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import Link from "next/link";

import {
  PageHeader,
} from "@/components/common/PageHeader";

import {
  Card,
} from "@/components/common/Card";

import {
  ApiListeningResponse,
  ApiMemoriesResponse,
  ApiRemindersResponse,
  ApiStatusResponse,
} from "@/types/api";

import {
  formatDateTime,
  formatMemorySchedule,
  parseDateTime,
} from "@/lib/formatters";

import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Bell,
  Brain,
  CheckCircle2,
  Clock,
  History,
  Mic,
  MicOff,
  RefreshCw,
  Search,
  Sparkles,
} from "lucide-react";


export default function DashboardPage() {
  const [
    statusResponse,
    setStatusResponse,
  ] =
    useState<ApiStatusResponse | null>(
      null,
    );

  const [
    memoriesResponse,
    setMemoriesResponse,
  ] =
    useState<ApiMemoriesResponse | null>(
      null,
    );

  const [
    remindersResponse,
    setRemindersResponse,
  ] =
    useState<ApiRemindersResponse | null>(
      null,
    );

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    changingListening,
    setChangingListening,
  ] =
    useState(false);

  const [
    feedback,
    setFeedback,
  ] =
    useState<{
      type:
        | "success"
        | "error";

      text: string;
    } | null>(
      null,
    );


  const loadDashboardData =
    useCallback(
      async (
        showLoading = true,
      ) => {
        if (showLoading) {
          setLoading(true);
        }

        try {
          const [
            statusResult,
            memoriesResult,
            remindersResult,
          ] =
            await Promise.allSettled([
              fetch(
                "/api/status",
                {
                  cache:
                    "no-store",
                },
              ).then(
                (
                  response,
                ) =>
                  response.json(),
              ),

              fetch(
                "/api/memories",
                {
                  cache:
                    "no-store",
                },
              ).then(
                (
                  response,
                ) =>
                  response.json(),
              ),

              fetch(
                "/api/reminders",
                {
                  cache:
                    "no-store",
                },
              ).then(
                (
                  response,
                ) =>
                  response.json(),
              ),
            ]);


          if (
            statusResult.status ===
            "fulfilled"
          ) {
            setStatusResponse(
              statusResult.value as ApiStatusResponse,
            );
          } else {
            setStatusResponse({
              available:
                false,

              error:
                "Unable to reach EchoMind.",
            });
          }


          if (
            memoriesResult.status ===
            "fulfilled"
          ) {
            setMemoriesResponse(
              memoriesResult.value as ApiMemoriesResponse,
            );
          } else {
            setMemoriesResponse({
              available:
                false,

              error:
                "Unable to load memories.",
            });
          }


          if (
            remindersResult.status ===
            "fulfilled"
          ) {
            setRemindersResponse(
              remindersResult.value as ApiRemindersResponse,
            );
          } else {
            setRemindersResponse({
              available:
                false,

              error:
                "Unable to load reminders.",
            });
          }

        } catch {
          setStatusResponse({
            available:
              false,

            error:
              "Unable to reach EchoMind.",
          });

          setMemoriesResponse({
            available:
              false,

            error:
              "Unable to load memories.",
          });

          setRemindersResponse({
            available:
              false,

            error:
              "Unable to load reminders.",
          });

        } finally {
          if (showLoading) {
            setLoading(false);
          }
        }
      },
      [],
    );


  useEffect(
    () => {
      loadDashboardData();

      const interval =
        window.setInterval(
          () => {
            loadDashboardData(
              false,
            );
          },
          5000,
        );

      return () => {
        window.clearInterval(
          interval,
        );
      };
    },
    [
      loadDashboardData,
    ],
  );


  const status =
    statusResponse?.status;

  const isAvailable =
    statusResponse?.available ===
      true &&
    status !== undefined;

  const listeningActive =
    status?.listening ===
    "active";

  const listeningStateText =
    listeningActive
      ? "On"
      : status?.listening ===
          "paused"
      ? "Paused"
      : "Unavailable";


  const memories =
    useMemo(
      () => {
        if (
          memoriesResponse?.available &&
          memoriesResponse.memories
        ) {
          return memoriesResponse.memories;
        }

        return [];
      },
      [
        memoriesResponse,
      ],
    );


  const reminders =
    useMemo(
      () => {
        if (
          remindersResponse?.available &&
          remindersResponse.reminders
        ) {
          return remindersResponse.reminders;
        }

        return [];
      },
      [
        remindersResponse,
      ],
    );


  const latestMemory =
    useMemo(
      () => {
        if (
          memories.length ===
          0
        ) {
          return null;
        }

        return [
          ...memories,
        ].sort(
          (
            first,
            second,
          ) =>
            second.id -
            first.id,
        )[0];
      },
      [
        memories,
      ],
    );


  const pendingReminders =
    useMemo(
      () =>
        reminders
          .filter(
            (
              reminder,
            ) =>
              reminder.status
                .trim()
                .toLowerCase() ===
              "pending",
          )
          .sort(
            (
              first,
              second,
            ) => {
              const firstDate =
                parseDateTime(
                  first.reminder_time,
                );

              const secondDate =
                parseDateTime(
                  second.reminder_time,
                );

              if (
                firstDate &&
                secondDate
              ) {
                return (
                  firstDate.getTime() -
                  secondDate.getTime()
                );
              }

              if (firstDate) {
                return -1;
              }

              if (secondDate) {
                return 1;
              }

              return 0;
            },
          ),
      [
        reminders,
      ],
    );


  const nextReminder =
    useMemo(
      () => {
        const now =
          new Date();

        const futureReminder =
          pendingReminders.find(
            (
              reminder,
            ) => {
              const parsed =
                parseDateTime(
                  reminder.reminder_time,
                );

              return (
                parsed !==
                  null &&
                parsed >= now
              );
            },
          );

        return (
          futureReminder ??
          pendingReminders[0] ??
          null
        );
      },
      [
        pendingReminders,
      ],
    );


  const handleListeningToggle =
    async () => {
      if (
        !isAvailable ||
        changingListening
      ) {
        return;
      }

      setChangingListening(
        true,
      );

      setFeedback(
        null,
      );

      const newState =
        !listeningActive;

      try {
        const response =
          await fetch(
            "/api/listening",
            {
              method:
                "POST",

              headers: {
                "Content-Type":
                  "application/json",
              },

              body:
                JSON.stringify({
                  enabled:
                    newState,
                }),

              cache:
                "no-store",
            },
          );

        const result =
          (await response.json()) as ApiListeningResponse;

        if (
          !response.ok ||
          result.available ===
            false ||
          result.success !==
            true
        ) {
          throw new Error(
            result.error ||
            "Unable to change listening state.",
          );
        }

        setFeedback({
          type:
            "success",

          text:
            newState
              ? "EchoMind listening resumed."
              : "EchoMind listening paused.",
        });

        await loadDashboardData(
          false,
        );

      } catch (
        error: unknown
      ) {
        setFeedback({
          type:
            "error",

          text:
            error instanceof Error
              ? error.message
              : "Unable to change listening state.",
        });

      } finally {
        setChangingListening(
          false,
        );
      }
    };


  return (
    <div className="space-y-6">

      <PageHeader
        title="Dashboard"
        description="Your EchoMind memory, reminder and system overview."
        badge={
          isAvailable
            ? "System Connected"
            : undefined
        }
        actions={
          <button
            type="button"
            onClick={() =>
              loadDashboardData()
            }
            disabled={
              loading
            }
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm transition hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700 disabled:opacity-50"
          >
            <RefreshCw
              className={`h-3.5 w-3.5 ${
                loading
                  ? "animate-spin"
                  : ""
              }`}
            />

            Refresh
          </button>
        }
      />


      {feedback && (
        <div
          className={`flex items-start gap-3 rounded-2xl border px-4 py-3 text-xs shadow-sm ${
            feedback.type ===
            "success"
              ? "border-emerald-200 bg-emerald-50 text-emerald-900"
              : "border-rose-200 bg-rose-50 text-rose-900"
          }`}
        >
          {feedback.type ===
          "success" ? (
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
          ) : (
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600" />
          )}

          <span className="font-medium">
            {feedback.text}
          </span>
        </div>
      )}


      {!loading &&
        !isAvailable && (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 shadow-sm">

            <div className="flex items-start gap-3">

              <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />

              <div>
                <h3 className="text-sm font-bold text-amber-950">
                  EchoMind backend is offline
                </h3>

                <p className="mt-1 text-xs leading-relaxed text-amber-800">
                  Start the Python EchoMind application and refresh this dashboard.
                </p>
              </div>

            </div>
          </div>
        )}


      {!loading &&
        isAvailable && (
          <div className="rounded-2xl border border-emerald-200/80 bg-gradient-to-r from-emerald-50 to-white p-5 shadow-sm">

            <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">

              <div className="flex items-start gap-3">

                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700">
                  <CheckCircle2 className="h-5 w-5" />
                </div>

                <div>
                  <h3 className="text-sm font-bold text-emerald-950">
                    EchoMind is ready
                  </h3>

                  <p className="mt-1 text-xs text-emerald-700">
                    Memory database and dashboard services are connected.
                  </p>
                </div>

              </div>

              <span className="inline-flex w-fit items-center gap-2 rounded-full bg-white px-3 py-1.5 text-[11px] font-bold text-emerald-700 shadow-sm ring-1 ring-emerald-200">

                <span className="h-2 w-2 rounded-full bg-emerald-500" />

                Online

              </span>

            </div>

          </div>
        )}


      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">

        <Card
          title="Memories"
          subtitle="Active saved information"
        >
          {loading ? (
            <div className="animate-pulse">
              <div className="h-8 w-16 rounded bg-slate-200" />
            </div>
          ) : (
            <div className="flex items-center justify-between">

              <div>
                <p className="text-3xl font-bold tracking-tight text-slate-950">
                  {
                    memoriesResponse?.available
                      ? memories.length
                      : "--"
                  }
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  Saved memories
                </p>
              </div>

              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
                <Brain className="h-5 w-5" />
              </div>

            </div>
          )}

          <div className="mt-4 border-t border-slate-100 pt-3">
            <Link
              href="/memories"
              className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-600 transition hover:text-indigo-800"
            >
              View memories

              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

        </Card>


        <Card
          title="Reminders"
          subtitle="Scheduled notifications"
        >
          {loading ? (
            <div className="animate-pulse">
              <div className="h-8 w-16 rounded bg-slate-200" />
            </div>
          ) : (
            <div className="flex items-center justify-between">

              <div>
                <p className="text-3xl font-bold tracking-tight text-slate-950">
                  {
                    remindersResponse?.available
                      ? reminders.length
                      : "--"
                  }
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  {pendingReminders.length} pending
                </p>
              </div>

              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-amber-50 text-amber-600">
                <Bell className="h-5 w-5" />
              </div>

            </div>
          )}

          <div className="mt-4 border-t border-slate-100 pt-3">
            <Link
              href="/reminders"
              className="inline-flex items-center gap-1.5 text-xs font-bold text-amber-600 transition hover:text-amber-800"
            >
              View reminders

              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

        </Card>


        <Card
          title="Listening"
          subtitle="Conversation capture"
        >
          {loading ? (
            <div className="animate-pulse">
              <div className="h-8 w-20 rounded bg-slate-200" />
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between">

                <div>
                  <p className="text-2xl font-bold text-slate-950">
                    {isAvailable
                      ? listeningStateText
                      : "--"}
                  </p>

                  <p className="mt-1 text-xs text-slate-500">
                    {listeningActive
                      ? "Microphone capture enabled"
                      : "Microphone capture paused"}
                  </p>
                </div>

                <div
                  className={`flex h-11 w-11 items-center justify-center rounded-2xl ${
                    listeningActive
                      ? "bg-emerald-50 text-emerald-600"
                      : "bg-slate-100 text-slate-500"
                  }`}
                >
                  {listeningActive ? (
                    <Mic className="h-5 w-5" />
                  ) : (
                    <MicOff className="h-5 w-5" />
                  )}
                </div>

              </div>

              <div className="mt-4 border-t border-slate-100 pt-3">

                <button
                  type="button"
                  onClick={
                    handleListeningToggle
                  }
                  disabled={
                    !isAvailable ||
                    changingListening
                  }
                  className={`inline-flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-bold transition disabled:cursor-not-allowed disabled:opacity-50 ${
                    listeningActive
                      ? "bg-rose-50 text-rose-700 hover:bg-rose-100"
                      : "bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
                  }`}
                >

                  {changingListening ? (
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  ) : listeningActive ? (
                    <MicOff className="h-3.5 w-3.5" />
                  ) : (
                    <Mic className="h-3.5 w-3.5" />
                  )}

                  {changingListening
                    ? "Updating..."
                    : listeningActive
                    ? "Pause Listening"
                    : "Resume Listening"}

                </button>

              </div>
            </>
          )}

        </Card>


        <Card
          title="System"
          subtitle="EchoMind core status"
        >
          {loading ? (
            <div className="animate-pulse">
              <div className="h-8 w-24 rounded bg-slate-200" />
            </div>
          ) : (
            <div className="flex items-center justify-between">

              <div>

                <p className="text-2xl font-bold text-slate-950">
                  {isAvailable
                    ? "Connected"
                    : "Offline"}
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  Database{" "}
                  {status?.database ??
                    "unavailable"}
                </p>

              </div>

              <div
                className={`flex h-11 w-11 items-center justify-center rounded-2xl ${
                  isAvailable
                    ? "bg-sky-50 text-sky-600"
                    : "bg-slate-100 text-slate-400"
                }`}
              >
                <Activity className="h-5 w-5" />
              </div>

            </div>
          )}

        </Card>

      </div>


      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">

        <Card
          title="Latest Memory"
          subtitle="Most recently stored active memory"
          action={
            <Link
              href="/memories"
              className="inline-flex items-center gap-1 text-[11px] font-bold text-indigo-600 hover:text-indigo-800"
            >
              View all

              <ArrowRight className="h-3 w-3" />
            </Link>
          }
        >
          {loading ? (
            <div className="animate-pulse space-y-3">
              <div className="h-5 w-1/3 rounded bg-slate-200" />

              <div className="h-4 w-full rounded bg-slate-200" />

              <div className="h-4 w-2/3 rounded bg-slate-200" />
            </div>
          ) : latestMemory ? (
            <div>

              <div className="flex flex-wrap items-center gap-2">

                <span className="rounded-lg border border-indigo-100 bg-indigo-50 px-2.5 py-1 text-[10px] font-bold text-indigo-700">
                  {latestMemory.category}
                </span>

                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[9px] font-bold text-emerald-700">
                  ACTIVE
                </span>

              </div>

              <h3 className="mt-3 text-base font-bold text-slate-950">
                {latestMemory.title}
              </h3>

              <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-slate-600">
                {latestMemory.content}
              </p>

              <div className="mt-4 flex items-center gap-1.5 border-t border-slate-100 pt-3 text-xs text-slate-500">

                <Clock className="h-3.5 w-3.5" />

                {formatMemorySchedule(
                  latestMemory.date,
                  latestMemory.time,
                )}

              </div>

            </div>
          ) : (
            <div className="py-4 text-center">

              <Brain className="mx-auto h-7 w-7 text-slate-300" />

              <p className="mt-2 text-xs font-semibold text-slate-600">
                No memories stored yet
              </p>

            </div>
          )}
        </Card>


        <Card
          title="Next Reminder"
          subtitle="Your nearest pending notification"
          action={
            <Link
              href="/reminders"
              className="inline-flex items-center gap-1 text-[11px] font-bold text-amber-600 hover:text-amber-800"
            >
              View all

              <ArrowRight className="h-3 w-3" />
            </Link>
          }
        >
          {loading ? (
            <div className="animate-pulse space-y-3">
              <div className="h-5 w-1/3 rounded bg-slate-200" />

              <div className="h-4 w-full rounded bg-slate-200" />

              <div className="h-4 w-2/3 rounded bg-slate-200" />
            </div>
          ) : nextReminder ? (
            <div>

              <div className="flex items-center gap-2">

                <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-2.5 py-1 text-[10px] font-bold text-amber-700 ring-1 ring-amber-600/15">

                  <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />

                  PENDING

                </span>

                <span className="text-[10px] text-slate-400">
                  Smart Reminder
                </span>

              </div>

              <h3 className="mt-3 text-base font-bold text-slate-950">
                {nextReminder.title}
              </h3>

              <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-slate-600">
                {nextReminder.content}
              </p>

              <div className="mt-4 flex items-center gap-2 rounded-xl border border-amber-100 bg-amber-50/60 px-3 py-2.5">

                <Bell className="h-4 w-4 shrink-0 text-amber-600" />

                <div>

                  <p className="text-[10px] font-semibold uppercase tracking-wide text-amber-700">
                    Reminder time
                  </p>

                  <p className="mt-0.5 text-xs font-bold text-slate-800">
                    {formatDateTime(
                      nextReminder.reminder_time,
                    )}
                  </p>

                </div>

              </div>

            </div>
          ) : (
            <div className="py-4 text-center">

              <CheckCircle2 className="mx-auto h-7 w-7 text-emerald-300" />

              <p className="mt-2 text-xs font-semibold text-slate-600">
                No pending reminders
              </p>

              <p className="mt-1 text-[10px] text-slate-400">
                You&apos;re all caught up.
              </p>

            </div>
          )}
        </Card>

      </div>


      <div className="space-y-3">

        <div>

          <div className="flex items-center gap-2">

            <Sparkles className="h-4 w-4 text-indigo-500" />

            <h2 className="text-base font-bold text-slate-950">
              EchoMind Workspace
            </h2>

          </div>

          <p className="mt-1 text-xs text-slate-500">
            Access your memories, retrieval, reminders and history.
          </p>

        </div>


        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">

          <Link
            href="/memories"
            className="group rounded-2xl border border-slate-200/80 bg-white/90 p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-md"
          >

            <div className="flex items-center gap-3">

              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 transition group-hover:bg-indigo-600 group-hover:text-white">
                <Brain className="h-5 w-5" />
              </div>

              <div>

                <h3 className="text-sm font-bold text-slate-900">
                  Memories
                </h3>

                <p className="mt-0.5 text-[11px] text-slate-500">
                  Browse and manage saved information
                </p>

              </div>

            </div>

          </Link>


          <Link
            href="/search"
            className="group rounded-2xl border border-slate-200/80 bg-white/90 p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-sky-200 hover:shadow-md"
          >

            <div className="flex items-center gap-3">

              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-50 text-sky-600 transition group-hover:bg-sky-600 group-hover:text-white">
                <Search className="h-5 w-5" />
              </div>

              <div>

                <h3 className="text-sm font-bold text-slate-900">
                  Find a Memory
                </h3>

                <p className="mt-0.5 text-[11px] text-slate-500">
                  Semantic memory retrieval
                </p>

              </div>

            </div>

          </Link>


          <Link
            href="/reminders"
            className="group rounded-2xl border border-slate-200/80 bg-white/90 p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-amber-200 hover:shadow-md"
          >

            <div className="flex items-center gap-3">

              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-50 text-amber-600 transition group-hover:bg-amber-500 group-hover:text-white">
                <Bell className="h-5 w-5" />
              </div>

              <div>

                <h3 className="text-sm font-bold text-slate-900">
                  Reminders
                </h3>

                <p className="mt-0.5 text-[11px] text-slate-500">
                  Smart scheduled notifications
                </p>

              </div>

            </div>

          </Link>


          <Link
            href="/history"
            className="group rounded-2xl border border-slate-200/80 bg-white/90 p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-purple-200 hover:shadow-md"
          >

            <div className="flex items-center gap-3">

              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-50 text-purple-600 transition group-hover:bg-purple-600 group-hover:text-white">
                <History className="h-5 w-5" />
              </div>

              <div>

                <h3 className="text-sm font-bold text-slate-900">
                  Memory History
                </h3>

                <p className="mt-0.5 text-[11px] text-slate-500">
                  Review replaced information
                </p>

              </div>

            </div>

          </Link>

        </div>

      </div>

    </div>
  );
}