"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import {
  ApiMemoriesResponse,
  ApiRemindersResponse,
  ApiStatusResponse,
} from "@/types/api";
import {
  Brain,
  Search,
  Bell,
  History,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Mic,
  ArrowRight,
  Activity,
  Bookmark,
} from "lucide-react";

export default function DashboardPage() {
  const [statusResponse, setStatusResponse] = useState<ApiStatusResponse | null>(null);
  const [memoryCount, setMemoryCount] = useState<number | null>(null);
  const [reminderCount, setReminderCount] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const loadDashboardData = useCallback(async () => {
    setLoading(true);

    try {
      // Fetch status, memories count, and reminders count in parallel
      const [statusRes, memoriesRes, remindersRes] = await Promise.allSettled([
        fetch("/api/status", { cache: "no-store" }).then((r) => r.json()),
        fetch("/api/memories", { cache: "no-store" }).then((r) => r.json()),
        fetch("/api/reminders", { cache: "no-store" }).then((r) => r.json()),
      ]);

      if (statusRes.status === "fulfilled") {
        setStatusResponse(statusRes.value as ApiStatusResponse);
      } else {
        setStatusResponse({ available: false, error: "Unable to reach assistant" });
      }

      if (memoriesRes.status === "fulfilled") {
        const memData = memoriesRes.value as ApiMemoriesResponse;
        setMemoryCount(memData.available && memData.memories ? memData.memories.length : null);
      } else {
        setMemoryCount(null);
      }

      if (remindersRes.status === "fulfilled") {
        const remData = remindersRes.value as ApiRemindersResponse;
        setReminderCount(remData.available && remData.reminders ? remData.reminders.length : null);
      } else {
        setReminderCount(null);
      }
    } catch {
      setStatusResponse({ available: false, error: "Unable to reach assistant" });
      setMemoryCount(null);
      setReminderCount(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const isAvailable = statusResponse?.available === true && statusResponse.status !== undefined;
  const status = statusResponse?.status;

  // Listening setting interpretation
  const listeningStateText =
    status?.listening === "active" ? "On" : status?.listening === "paused" ? "Paused" : "Unavailable";

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="A quick view of what EchoMind remembers for you."
        actions={
          <button
            type="button"
            onClick={loadDashboardData}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 transition-colors cursor-pointer"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-indigo-600" : ""}`} />
            <span>Refresh</span>
          </button>
        }
      />

      {/* Friendly Backend Unavailable State */}
      {!loading && !isAvailable && (
        <div className="rounded-xl border border-amber-200 bg-amber-50/80 p-5 text-amber-950 shadow-xs">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 shrink-0 text-amber-600 mt-0.5" />
            <div className="flex-1 space-y-1">
              <h3 className="text-sm font-semibold text-amber-950">
                EchoMind is currently unavailable.
              </h3>
              <p className="text-xs text-amber-800 leading-relaxed">
                Please check back in a moment or click Refresh to try again.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Friendly Backend Online Notice */}
      {!loading && isAvailable && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-5 text-emerald-950 shadow-xs">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-emerald-950">
                EchoMind is ready
              </h3>
              <p className="mt-0.5 text-xs text-emerald-800">
                Your saved memories and reminders are available.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Clean Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* 1. Saved Memories */}
        <Card title="Memories" subtitle="Saved knowledge">
          {loading ? (
            <div className="animate-pulse space-y-2 py-1">
              <div className="h-4 bg-slate-200 rounded w-20"></div>
              <div className="h-6 bg-slate-200 rounded w-28"></div>
            </div>
          ) : (
            <div className="flex items-center justify-between pt-1">
              <div>
                <p className="text-2xl font-bold text-slate-900">
                  {memoryCount !== null ? memoryCount : "--"}
                </p>
                <p className="text-xs font-medium text-slate-500">
                  {memoryCount !== null ? "Saved" : "Unavailable"}
                </p>
              </div>
              <div className="rounded-lg bg-indigo-50 p-2.5 text-indigo-600">
                <Brain className="h-5 w-5" />
              </div>
            </div>
          )}
          <div className="mt-3 border-t border-slate-100 pt-2.5">
            <Link
              href="/memories"
              className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-700"
            >
              View memories <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </Card>

        {/* 2. Total Reminders */}
        <Card title="Reminders" subtitle="Commitments & alerts">
          {loading ? (
            <div className="animate-pulse space-y-2 py-1">
              <div className="h-4 bg-slate-200 rounded w-20"></div>
              <div className="h-6 bg-slate-200 rounded w-28"></div>
            </div>
          ) : (
            <div className="flex items-center justify-between pt-1">
              <div>
                <p className="text-2xl font-bold text-slate-900">
                  {reminderCount !== null ? reminderCount : "--"}
                </p>
                <p className="text-xs font-medium text-slate-500">
                  {reminderCount !== null ? "Total" : "Unavailable"}
                </p>
              </div>
              <div className="rounded-lg bg-amber-50 p-2.5 text-amber-600">
                <Bell className="h-5 w-5" />
              </div>
            </div>
          )}
          <div className="mt-3 border-t border-slate-100 pt-2.5">
            <Link
              href="/reminders"
              className="inline-flex items-center gap-1 text-xs font-semibold text-amber-600 hover:text-amber-700"
            >
              View reminders <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </Card>

        {/* 3. Listening Setting */}
        <Card title="Listening Setting" subtitle="Voice capture preference">
          {loading ? (
            <div className="animate-pulse space-y-2 py-1">
              <div className="h-4 bg-slate-200 rounded w-20"></div>
              <div className="h-6 bg-slate-200 rounded w-28"></div>
            </div>
          ) : (
            <div className="flex items-center justify-between pt-1">
              <div>
                <p className="text-2xl font-bold text-slate-900">
                  {isAvailable ? listeningStateText : "--"}
                </p>
                <p className="text-xs font-medium text-slate-500">
                  {isAvailable
                    ? status?.listening === "active"
                      ? "Listening allowed"
                      : "Listening paused"
                    : "Unavailable"}
                </p>
              </div>
              <div
                className={`rounded-lg p-2.5 ${
                  status?.listening === "active"
                    ? "bg-emerald-50 text-emerald-600"
                    : "bg-slate-100 text-slate-400"
                }`}
              >
                <Mic className="h-5 w-5" />
              </div>
            </div>
          )}
          <div className="mt-3 border-t border-slate-100 pt-2.5">
            <span
              className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                status?.listening === "active"
                  ? "bg-emerald-100 text-emerald-800"
                  : "bg-slate-100 text-slate-600"
              }`}
            >
              {status?.listening === "active" ? "On" : "Paused"}
            </span>
          </div>
        </Card>

        {/* 4. Dashboard / EchoMind Status */}
        <Card title="EchoMind" subtitle="Assistant status">
          {loading ? (
            <div className="animate-pulse space-y-2 py-1">
              <div className="h-4 bg-slate-200 rounded w-20"></div>
              <div className="h-6 bg-slate-200 rounded w-28"></div>
            </div>
          ) : (
            <div className="flex items-center justify-between pt-1">
              <div>
                <p className="text-2xl font-bold text-slate-900">
                  {isAvailable ? "Connected" : "Offline"}
                </p>
                <p className="text-xs font-medium text-slate-500">
                  {isAvailable ? "Dashboard ready" : "Not connected"}
                </p>
              </div>
              <div
                className={`rounded-lg p-2.5 ${
                  isAvailable ? "bg-indigo-50 text-indigo-600" : "bg-slate-100 text-slate-400"
                }`}
              >
                <Activity className="h-5 w-5" />
              </div>
            </div>
          )}
          <div className="mt-3 border-t border-slate-100 pt-2.5">
            <span
              className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                isAvailable ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-600"
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  isAvailable ? "bg-emerald-500" : "bg-slate-400"
                }`}
              ></span>
              {isAvailable ? "Ready" : "Unavailable"}
            </span>
          </div>
        </Card>
      </div>

      {/* Quick Navigation Cards for Normal Users */}
      <div className="space-y-3">
        <h2 className="text-base font-semibold text-slate-900">
          What would you like to do?
        </h2>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Link
            href="/memories"
            className="group rounded-xl border border-slate-200 bg-white p-5 transition-all hover:border-indigo-200 hover:shadow-xs"
          >
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-indigo-50 p-2.5 text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                <Brain className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Memories</h3>
                <p className="text-xs text-slate-500">Browse saved memories</p>
              </div>
            </div>
          </Link>

          <Link
            href="/search"
            className="group rounded-xl border border-slate-200 bg-white p-5 transition-all hover:border-indigo-200 hover:shadow-xs"
          >
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-sky-50 p-2.5 text-sky-600 group-hover:bg-sky-600 group-hover:text-white transition-colors">
                <Search className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Find a Memory</h3>
                <p className="text-xs text-slate-500">Search what you mentioned</p>
              </div>
            </div>
          </Link>

          <Link
            href="/reminders"
            className="group rounded-xl border border-slate-200 bg-white p-5 transition-all hover:border-indigo-200 hover:shadow-xs"
          >
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-amber-50 p-2.5 text-amber-600 group-hover:bg-amber-600 group-hover:text-white transition-colors">
                <Bell className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Reminders</h3>
                <p className="text-xs text-slate-500">Upcoming commitments</p>
              </div>
            </div>
          </Link>

          <Link
            href="/history"
            className="group rounded-xl border border-slate-200 bg-white p-5 transition-all hover:border-indigo-200 hover:shadow-xs"
          >
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-purple-50 p-2.5 text-purple-600 group-hover:bg-purple-600 group-hover:text-white transition-colors">
                <History className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Memory History</h3>
                <p className="text-xs text-slate-500">Replaced earlier notes</p>
              </div>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}
