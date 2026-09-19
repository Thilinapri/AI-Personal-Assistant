"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import { ApiMemoryHistoryResponse, Memory } from "@/types/api";
import {
  History,
  RefreshCw,
  AlertTriangle,
  Calendar,
  Clock,
  Info,
  Terminal,
  FileQuestion,
  Repeat,
  Archive,
} from "lucide-react";

export default function HistoryPage() {
  const [response, setResponse] = useState<ApiMemoryHistoryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/memories/history", { cache: "no-store" });
      const data: ApiMemoryHistoryResponse = await res.json();
      setResponse(data);
    } catch (err: unknown) {
      setResponse({
        available: false,
        error: err instanceof Error ? err.message : "Failed to load memory history",
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  // Order history by descending memory ID (newer memory records first)
  const historyMemories = useMemo(() => {
    if (!response?.available || !response.memories) return [];
    return [...response.memories].sort((a, b) => b.id - a.id);
  }, [response]);

  const isAvailable = response?.available === true;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Memory History"
        description="Audit trail of superseded memories replaced by updated knowledge."
        badge={
          loading
            ? "Loading..."
            : isAvailable
            ? `${historyMemories.length} Superseded Record${historyMemories.length === 1 ? "" : "s"}`
            : "Backend Offline"
        }
        actions={
          <button
            type="button"
            onClick={fetchHistory}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 transition-colors cursor-pointer"
          >
            <RefreshCw
              className={`h-3.5 w-3.5 ${
                loading ? "animate-spin text-indigo-600" : ""
              }`}
            />
            <span>Refresh</span>
          </button>
        }
      />

      {/* Explanatory notice required at top of page */}
      <div className="rounded-xl border border-purple-100 bg-purple-50/60 p-4 text-xs text-purple-950 shadow-xs">
        <div className="flex items-start gap-2.5">
          <Info className="h-4 w-4 shrink-0 text-purple-600 mt-0.5" />
          <div className="space-y-1 leading-relaxed">
            <p className="font-semibold text-purple-950">
              Superseded Memory Archive
            </p>
            <p className="text-purple-800">
              History contains memories that were previously active but were later replaced by newer information.
            </p>
          </div>
        </div>
      </div>

      {/* Backend Unavailable State */}
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
                  The Next.js API proxy cannot connect to the EchoMind Flask API to load memory history.
                </p>
                {response?.error && (
                  <p className="mt-1 font-mono text-[11px] text-rose-700 bg-rose-100/70 px-2 py-1 rounded inline-block">
                    Error: {response.error}
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

      {/* Loading Skeletons */}
      {loading && (
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div
              key={i}
              className="animate-pulse rounded-xl border border-slate-200 bg-white p-5 shadow-xs space-y-3"
            >
              <div className="flex items-center justify-between">
                <div className="h-5 bg-slate-200 rounded w-1/3"></div>
                <div className="h-5 bg-slate-200 rounded w-24"></div>
              </div>
              <div className="h-4 bg-slate-200 rounded w-full"></div>
              <div className="h-4 bg-slate-200 rounded w-2/3"></div>
              <div className="pt-2 border-t border-slate-100 flex gap-4">
                <div className="h-3 bg-slate-200 rounded w-24"></div>
                <div className="h-3 bg-slate-200 rounded w-24"></div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* History List Content */}
      {!loading && isAvailable && (
        <>
          {historyMemories.length === 0 ? (
            /* Empty History State */
            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center shadow-xs">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-purple-50 text-purple-600">
                <Archive className="h-6 w-6" />
              </div>
              <h3 className="mt-3 text-base font-semibold text-slate-900">
                No Superseded Memories
              </h3>
              <p className="mt-1 text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
                There are currently no superseded records in the memory archive. When existing memories are replaced or updated with new information, earlier revisions are archived here.
              </p>
            </div>
          ) : (
            /* Superseded Memory Cards */
            <div className="space-y-4">
              {historyMemories.map((memory) => {
                const isDuplicate = memory.seen_count > 1;
                const hasSupersededAnother = memory.supersedes_id !== null && memory.supersedes_id !== undefined;

                return (
                  <div
                    key={memory.id}
                    className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs transition-all hover:border-purple-200 hover:shadow-sm"
                  >
                    {/* Header Row: Category, Title & Badges */}
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-700 border border-slate-200">
                            {memory.category || "General"}
                          </span>
                          <h2 className="text-base font-semibold text-slate-900">
                            {memory.title}
                          </h2>
                        </div>
                      </div>

                      {/* Lifecycle Badges: SUPERSEDED always, DUPLICATE SEEN when seen_count > 1, NEVER ACTIVE */}
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span className="rounded-full bg-purple-50 px-2.5 py-0.5 text-[10px] font-bold tracking-wide text-purple-700 ring-1 ring-inset ring-purple-600/20">
                          SUPERSEDED
                        </span>

                        {isDuplicate && (
                          <span className="rounded-full bg-amber-50 px-2.5 py-0.5 text-[10px] font-bold tracking-wide text-amber-800 ring-1 ring-inset ring-amber-600/20">
                            DUPLICATE SEEN &times;{memory.seen_count}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Content */}
                    <p className="mt-3 text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {memory.content}
                    </p>

                    {/* supersedes_id Informational Note: means this row originally replaced another memory */}
                    {hasSupersededAnother && (
                      <div className="mt-3 inline-flex items-center gap-1.5 rounded-md bg-purple-50/70 border border-purple-100 px-2.5 py-1 text-xs text-purple-900">
                        <Repeat className="h-3.5 w-3.5 text-purple-600 shrink-0" />
                        <span>Originally replaced Memory #{memory.supersedes_id}</span>
                      </div>
                    )}

                    {/* Metadata Footer */}
                    <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-3 text-xs text-slate-500">
                      <div className="flex flex-wrap items-center gap-4">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3.5 w-3.5 text-slate-400" />
                          <span>{memory.date && memory.date.trim() ? memory.date : "No date set"}</span>
                        </div>

                        <div className="flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5 text-slate-400" />
                          <span>{memory.time && memory.time.trim() ? memory.time : "No time set"}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 text-[11px] text-slate-400">
                        <span>Status: <strong className="font-mono text-slate-600">{memory.status}</strong></span>
                        <span>&bull;</span>
                        <span>Seen: {memory.seen_count}</span>
                        <span>&bull;</span>
                        <span className="font-mono">ID #{memory.id}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}
