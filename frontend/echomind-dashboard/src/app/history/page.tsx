"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { ApiMemoryHistoryResponse } from "@/types/api";
import {
  RefreshCw,
  AlertTriangle,
  Calendar,
  Clock,
  Info,
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
        description="Older information that was replaced when EchoMind learned something new."
        badge={
          loading
            ? "Loading..."
            : isAvailable
            ? `${historyMemories.length} Archived`
            : undefined
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

      {/* Explanatory notice at top of page */}
      <div className="rounded-xl border border-purple-100 bg-purple-50/60 p-4 text-xs text-purple-950 shadow-xs">
        <div className="flex items-start gap-2.5">
          <Info className="h-4 w-4 shrink-0 text-purple-600 mt-0.5" />
          <div className="space-y-1 leading-relaxed">
            <p className="font-semibold text-purple-950">
              Memory Archive
            </p>
            <p className="text-purple-800">
              This section stores earlier notes that were updated as EchoMind learned new details.
            </p>
          </div>
        </div>
      </div>

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
                No Replaced Memories
              </h3>
              <p className="mt-1 text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
                When saved memories are updated with new details, earlier versions will be kept here for your reference.
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

                      {/* Lifecycle Badges: REPLACED always, Mentioned X times when seen_count > 1 */}
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span className="rounded-full bg-purple-50 px-2.5 py-0.5 text-[10px] font-bold tracking-wide text-purple-700 ring-1 ring-inset ring-purple-600/20">
                          REPLACED
                        </span>

                        {isDuplicate && (
                          <span className="rounded-full bg-amber-50 px-2.5 py-0.5 text-[10px] font-semibold tracking-wide text-amber-800 ring-1 ring-inset ring-amber-600/20">
                            Mentioned {memory.seen_count} times
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Content */}
                    <p className="mt-3 text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {memory.content}
                    </p>

                    {/* Replaced note */}
                    <p className="mt-2 text-xs italic text-slate-500">
                      This memory was replaced by newer information.
                    </p>

                    {/* supersedes_id Informational Note */}
                    {hasSupersededAnother && (
                      <div className="mt-3 inline-flex items-center gap-1.5 rounded-md bg-purple-50/70 border border-purple-100 px-2.5 py-1 text-xs text-purple-900">
                        <Repeat className="h-3.5 w-3.5 text-purple-600 shrink-0" />
                        <span>Originally updated from an earlier note</span>
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
