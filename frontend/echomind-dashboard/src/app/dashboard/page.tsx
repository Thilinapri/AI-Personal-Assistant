"use client";

import React, {
  useCallback,
  useEffect,
  useState,
} from "react";

import Link from "next/link";

import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";

import {
  ApiListeningResponse,
  ApiMemoriesResponse,
  ApiRemindersResponse,
  ApiStatusResponse,
} from "@/types/api";

import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Bell,
  Brain,
  CheckCircle2,
  History,
  Mic,
  MicOff,
  RefreshCw,
  Search,
} from "lucide-react";

export default function DashboardPage() {
  const [statusResponse, setStatusResponse] =
    useState<ApiStatusResponse | null>(null);

  const [memoryCount, setMemoryCount] =
    useState<number | null>(null);

  const [reminderCount, setReminderCount] =
    useState<number | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [changingListening, setChangingListening] =
    useState(false);

  const [feedback, setFeedback] =
    useState<{
      type: "success" | "error";
      text: string;
    } | null>(null);

  const loadDashboardData = useCallback(
    async (showLoading = true) => {
      if (showLoading) {
        setLoading(true);
      }

      try {
        const [
          statusResult,
          memoriesResult,
          remindersResult,
        ] = await Promise.allSettled([
          fetch("/api/status", {
            cache: "no-store",
          }).then((response) => response.json()),

          fetch("/api/memories", {
            cache: "no-store",
          }).then((response) => response.json()),

          fetch("/api/reminders", {
            cache: "no-store",
          }).then((response) => response.json()),
        ]);

        if (statusResult.status === "fulfilled") {
          setStatusResponse(
            statusResult.value as ApiStatusResponse
          );
        } else {
          setStatusResponse({
            available: false,
            error: "Unable to reach EchoMind.",
          });
        }

        if (memoriesResult.status === "fulfilled") {
          const data =
            memoriesResult.value as ApiMemoriesResponse;

          setMemoryCount(
            data.available && data.memories
              ? data.memories.length
              : null
          );
        } else {
          setMemoryCount(null);
        }

        if (remindersResult.status === "fulfilled") {
          const data =
            remindersResult.value as ApiRemindersResponse;

          setReminderCount(
            data.available && data.reminders
              ? data.reminders.length
              : null
          );
        } else {
          setReminderCount(null);
        }
      } catch {
        setStatusResponse({
          available: false,
          error: "Unable to reach EchoMind.",
        });

        setMemoryCount(null);
        setReminderCount(null);
      } finally {
        if (showLoading) {
          setLoading(false);
        }
      }
    },
    []
  );

  useEffect(() => {
    loadDashboardData();

    const interval =
      window.setInterval(() => {
        loadDashboardData(false);
      }, 5000);

    return () => {
      window.clearInterval(interval);
    };
  }, [loadDashboardData]);

  const status =
    statusResponse?.status;

  const isAvailable =
    statusResponse?.available === true &&
    status !== undefined;

  const listeningActive =
    status?.listening === "active";

  const listeningStateText =
    listeningActive
      ? "On"
      : status?.listening === "paused"
        ? "Paused"
        : "Unavailable";

  const handleListeningToggle =
    async () => {
      if (
        !isAvailable ||
        changingListening
      ) {
        return;
      }

      setChangingListening(true);
      setFeedback(null);

      const newState =
        !listeningActive;

      try {
        const response =
          await fetch(
            "/api/listening",
            {
              method: "POST",

              headers: {
                "Content-Type":
                  "application/json",
              },

              body: JSON.stringify({
                enabled: newState,
              }),

              cache: "no-store",
            }
          );

        const result =
          (await response.json()) as ApiListeningResponse;

        if (
          !response.ok ||
          result.available === false ||
          result.success !== true
        ) {
          throw new Error(
            result.error ||
              "Unable to change listening state."
          );
        }

        setFeedback({
          type: "success",
          text: newState
            ? "EchoMind listening resumed."
            : "EchoMind listening paused.",
        });

        await loadDashboardData(false);
      } catch (error: unknown) {
        setFeedback({
          type: "error",
          text:
            error instanceof Error
              ? error.message
              : "Unable to change listening state.",
        });
      } finally {
        setChangingListening(false);
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
            disabled={loading}
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
            feedback.type === "success"
              ? "border-emerald-200 bg-emerald-50 text-emerald-900"
              : "border-rose-200 bg-rose-50 text-rose-900"
          }`}
        >
          {feedback.type === "success" ? (
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
                  {memoryCount ?? "--"}
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
                  {reminderCount ?? "--"}
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  Total reminders
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

      <div className="space-y-3">
        <div>
          <h2 className="text-base font-bold text-slate-950">
            EchoMind Workspace
          </h2>

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