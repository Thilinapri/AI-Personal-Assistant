"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import { ApiStatusResponse } from "@/types/api";
import {
  Mic,
  Brain,
  Search,
  Bell,
  History,
  ShieldCheck,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Database,
  Server,
  Activity,
  Info,
  Layers,
  Terminal,
} from "lucide-react";

export default function DashboardPage() {
  const [statusResponse, setStatusResponse] = useState<ApiStatusResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/status", { cache: "no-store" });
      const data: ApiStatusResponse = await res.json();
      setStatusResponse(data);
      setLastChecked(new Date());
    } catch (err: unknown) {
      setStatusResponse({
        available: false,
        error: err instanceof Error ? err.message : "Failed to query status proxy",
      });
      setLastChecked(new Date());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const isAvailable = statusResponse?.available === true && statusResponse.status !== undefined;
  const status = statusResponse?.status;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="System overview, listening preference, and backend connectivity."
        badge={
          loading
            ? "Checking..."
            : isAvailable
            ? "Backend Online"
            : "Backend Offline"
        }
        actions={
          <button
            type="button"
            onClick={fetchStatus}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-indigo-600" : ""}`} />
            <span>Refresh Status</span>
          </button>
        }
      />

      {/* Backend Unavailable Alert State */}
      {!loading && !isAvailable && (
        <div className="rounded-xl border border-rose-200 bg-rose-50/80 p-4 sm:p-5 text-rose-900 shadow-xs">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 shrink-0 text-rose-600 mt-0.5" />
            <div className="flex-1 space-y-2">
              <div>
                <h3 className="text-sm font-semibold text-rose-950">
                  Flask REST Backend Unavailable
                </h3>
                <p className="mt-0.5 text-xs text-rose-800 leading-relaxed">
                  The Next.js API proxy cannot reach the EchoMind Flask API. Ensure the Python backend service is running locally.
                </p>
                {statusResponse?.error && (
                  <p className="mt-1 font-mono text-[11px] text-rose-700 bg-rose-100/70 px-2 py-1 rounded inline-block">
                    Error: {statusResponse.error}
                  </p>
                )}
              </div>

              <div className="flex items-center gap-2 rounded-lg bg-rose-100/60 p-2.5 text-xs text-rose-900">
                <Terminal className="h-4 w-4 text-rose-700 shrink-0" />
                <span>To start the backend, run:</span>
                <code className="font-mono font-semibold text-rose-950 bg-white/80 px-1.5 py-0.5 rounded border border-rose-200">
                  python -m web.app
                </code>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Backend Online Notice */}
      {!loading && isAvailable && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-4 sm:p-5 text-emerald-950 shadow-xs">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600 mt-0.5" />
            <div className="flex-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-sm font-semibold text-emerald-950">
                  Flask REST API Connected Successfully
                </h3>
                {lastChecked && (
                  <span className="text-[11px] text-emerald-700">
                    Last polled: {lastChecked.toLocaleTimeString()}
                  </span>
                )}
              </div>
              <p className="mt-0.5 text-xs text-emerald-800">
                Next.js server proxy is communicating with the EchoMind Flask service. Dual frontends (Flask + Next.js) are active.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Real Backend Values Status Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* 1. EchoMind Application Status */}
        <Card
          title="Application"
          subtitle="EchoMind Core Identifier"
        >
          {loading ? (
            <div className="animate-pulse space-y-2 py-1">
              <div className="h-4 bg-slate-200 rounded w-24"></div>
              <div className="h-6 bg-slate-200 rounded w-32"></div>
            </div>
          ) : (
            <div className="flex items-center justify-between pt-1">
              <div>
                <p className="text-xs font-medium text-slate-500">Service Name</p>
                <p className="text-lg font-bold text-slate-900">
                  {status?.application ?? "Unavailable"}
                </p>
              </div>
              <div className="rounded-lg bg-indigo-50 p-2.5 text-indigo-600">
                <Layers className="h-5 w-5" />
              </div>
            </div>
          )}
          <div className="mt-3 border-t border-slate-100 pt-2.5">
            <span className="inline-flex items-center gap-1.5 text-xs text-slate-500">
              <span className={`h-2 w-2 rounded-full ${isAvailable ? "bg-emerald-500" : "bg-slate-300"}`}></span>
              {isAvailable ? "EchoMind Runtime" : "Awaiting Service"}
            </span>
          </div>
        </Card>

        {/* 2. Web / Backend Status */}
        <Card
          title="Web Backend"
          subtitle="Flask REST API Service"
        >
          {loading ? (
            <div className="animate-pulse space-y-2 py-1">
              <div className="h-4 bg-slate-200 rounded w-24"></div>
              <div className="h-6 bg-slate-200 rounded w-32"></div>
            </div>
          ) : (
            <div className="flex items-center justify-between pt-1">
              <div>
                <p className="text-xs font-medium text-slate-500">REST Status</p>
                <p className="text-lg font-bold capitalize text-slate-900">
                  {status?.web ?? "Offline"}
                </p>
              </div>
              <div className={`rounded-lg p-2.5 ${isAvailable ? "bg-emerald-50 text-emerald-600" : "bg-slate-100 text-slate-400"}`}>
                <Server className="h-5 w-5" />
              </div>
            </div>
          )}
          <div className="mt-3 border-t border-slate-100 pt-2.5">
            <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold ${
              status?.web === "running"
                ? "bg-emerald-100 text-emerald-800"
                : "bg-slate-100 text-slate-600"
            }`}>
              {status?.web === "running" ? "Online (Port 5000)" : "Not reachable"}
            </span>
          </div>
        </Card>

        {/* 3. Database Status */}
        <Card
          title="Database"
          subtitle="SQLite Storage Layer"
        >
          {loading ? (
            <div className="animate-pulse space-y-2 py-1">
              <div className="h-4 bg-slate-200 rounded w-24"></div>
              <div className="h-6 bg-slate-200 rounded w-32"></div>
            </div>
          ) : (
            <div className="flex items-center justify-between pt-1">
              <div>
                <p className="text-xs font-medium text-slate-500">Connection</p>
                <p className="text-lg font-bold capitalize text-slate-900">
                  {status?.database ?? "Unavailable"}
                </p>
              </div>
              <div className={`rounded-lg p-2.5 ${status?.database === "connected" ? "bg-emerald-50 text-emerald-600" : "bg-slate-100 text-slate-400"}`}>
                <Database className="h-5 w-5" />
              </div>
            </div>
          )}
          <div className="mt-3 border-t border-slate-100 pt-2.5">
            <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold ${
              status?.database === "connected"
                ? "bg-emerald-100 text-emerald-800"
                : "bg-amber-100 text-amber-800"
            }`}>
              {status?.database === "connected" ? "Connected (SQLite)" : "Disconnected"}
            </span>
          </div>
        </Card>

        {/* 4. Listening Status */}
        <Card
          title="Listening"
          subtitle="Listening Preference"
        >
          {loading ? (
            <div className="animate-pulse space-y-2 py-1">
              <div className="h-4 bg-slate-200 rounded w-24"></div>
              <div className="h-6 bg-slate-200 rounded w-32"></div>
            </div>
          ) : (
            <div className="flex items-center justify-between pt-1">
              <div>
                <p className="text-xs font-medium text-slate-500">Preference</p>
                <p className="text-lg font-bold capitalize text-slate-900">
                  {status?.listening ?? "Unavailable"}
                </p>
              </div>
              <div className={`rounded-lg p-2.5 ${status?.listening === "active" ? "bg-indigo-50 text-indigo-600" : "bg-slate-100 text-slate-400"}`}>
                <Mic className="h-5 w-5" />
              </div>
            </div>
          )}
          <div className="mt-3 border-t border-slate-100 pt-2.5">
            <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold ${
              status?.listening === "active"
                ? "bg-indigo-100 text-indigo-800"
                : "bg-slate-100 text-slate-600"
            }`}>
              {status?.listening === "active" ? "Active" : "Paused"}
            </span>
          </div>
        </Card>
      </div>

      {/* Architecture & Security Notice */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
        <div className="flex items-start gap-3">
          <Info className="h-5 w-5 text-indigo-600 mt-0.5 shrink-0" />
          <div className="space-y-1 text-xs sm:text-sm text-slate-700">
            <p className="font-semibold text-slate-900">
              Architecture Guarantee: Decoupled Server-Side Proxy
            </p>
            <p className="text-slate-600 leading-relaxed">
              Browser components communicate exclusively with Next.js internal route handlers (<code className="font-mono bg-slate-100 px-1 py-0.5 rounded text-slate-800">/api/status</code>). The backend address is isolated in the server-only <code className="font-mono bg-slate-100 px-1 py-0.5 rounded text-slate-800">ECHOMIND_API_URL</code> environment variable. No direct SQLite access or LLM credentials are ever exposed client-side.
            </p>
          </div>
        </div>
      </div>

      {/* Navigation Quick Access Grid (Placeholders preserved) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">
            EchoMind Modules (Placeholders)
          </h2>
          <span className="text-xs text-slate-500">Step 2: Status Connected Only</span>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Link
            href="/memories"
            className="group rounded-xl border border-slate-200 bg-white p-5 transition-all hover:border-indigo-200 hover:shadow-sm"
          >
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-indigo-50 p-2 text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                <Brain className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Memories</h3>
                <p className="text-xs text-slate-500">Placeholder (awaiting API hookup)</p>
              </div>
            </div>
          </Link>

          <Link
            href="/search"
            className="group rounded-xl border border-slate-200 bg-white p-5 transition-all hover:border-indigo-200 hover:shadow-sm"
          >
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-sky-50 p-2 text-sky-600 group-hover:bg-sky-600 group-hover:text-white transition-colors">
                <Search className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Semantic Search</h3>
                <p className="text-xs text-slate-500">Placeholder (awaiting API hookup)</p>
              </div>
            </div>
          </Link>

          <Link
            href="/reminders"
            className="group rounded-xl border border-slate-200 bg-white p-5 transition-all hover:border-indigo-200 hover:shadow-sm"
          >
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-amber-50 p-2 text-amber-600 group-hover:bg-amber-600 group-hover:text-white transition-colors">
                <Bell className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Reminders</h3>
                <p className="text-xs text-slate-500">Placeholder (awaiting API hookup)</p>
              </div>
            </div>
          </Link>

          <Link
            href="/history"
            className="group rounded-xl border border-slate-200 bg-white p-5 transition-all hover:border-indigo-200 hover:shadow-sm"
          >
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-purple-50 p-2 text-purple-600 group-hover:bg-purple-600 group-hover:text-white transition-colors">
                <History className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Memory History</h3>
                <p className="text-xs text-slate-500">Placeholder (awaiting API hookup)</p>
              </div>
            </div>
          </Link>

          <Link
            href="/privacy"
            className="group rounded-xl border border-slate-200 bg-white p-5 transition-all hover:border-indigo-200 hover:shadow-sm"
          >
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-emerald-50 p-2 text-emerald-600 group-hover:bg-emerald-600 group-hover:text-white transition-colors">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Privacy Gateway</h3>
                <p className="text-xs text-slate-500">Placeholder (awaiting API hookup)</p>
              </div>
            </div>
          </Link>

          <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50/50 p-5">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-slate-100 p-2 text-slate-500">
                <Activity className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-700">Proxy Health</h3>
                <p className="text-xs text-slate-500">Route Handler active</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
