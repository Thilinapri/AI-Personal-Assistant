"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import { ApiMemoriesResponse, Memory, MemoryCategory } from "@/types/api";
import {
  Brain,
  RefreshCw,
  AlertTriangle,
  Calendar,
  Clock,
  Bell,
  BellOff,
  Tag,
  Repeat,
  FileQuestion,
} from "lucide-react";

const CATEGORIES: MemoryCategory[] = [
  "All",
  "Reminder",
  "Task",
  "Shopping",
  "Note",
  "Preference",
  "Event",
];

export default function MemoriesPage() {
  const [response, setResponse] = useState<ApiMemoriesResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedCategory, setSelectedCategory] = useState<MemoryCategory>("All");

  const fetchMemories = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/memories", { cache: "no-store" });
      const data: ApiMemoriesResponse = await res.json();
      setResponse(data);
    } catch (err: unknown) {
      setResponse({
        available: false,
        error: err instanceof Error ? err.message : "Failed to load memories",
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMemories();
  }, [fetchMemories]);

  const allMemories = useMemo(() => {
    return response?.available && response.memories ? response.memories : [];
  }, [response]);

  const filteredMemories = useMemo(() => {
    if (selectedCategory === "All") {
      return allMemories;
    }
    return allMemories.filter(
      (m) => m.category.trim().toLowerCase() === selectedCategory.toLowerCase()
    );
  }, [allMemories, selectedCategory]);

  // Compute item count per category for pills
  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = { All: allMemories.length };
    for (const cat of CATEGORIES) {
      if (cat === "All") continue;
      counts[cat] = allMemories.filter(
        (m) => m.category.trim().toLowerCase() === cat.toLowerCase()
      ).length;
    }
    return counts;
  }, [allMemories]);

  const isAvailable = response?.available === true;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Memories"
        description="Important things EchoMind remembers for you."
        badge={
          loading
            ? "Loading..."
            : isAvailable
            ? `${allMemories.length} Saved`
            : undefined
        }
        actions={
          <button
            type="button"
            onClick={fetchMemories}
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

      {/* Friendly Backend Unavailable Alert */}
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

      {/* Category Filter Pills */}
      {isAvailable && (
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 pb-4">
          <span className="text-xs font-medium text-slate-500 mr-1 flex items-center gap-1">
            <Tag className="h-3.5 w-3.5" /> Filter:
          </span>
          {CATEGORIES.map((cat) => {
            const count = categoryCounts[cat] ?? 0;
            const isSelected = selectedCategory === cat;
            return (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedCategory(cat)}
                className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all cursor-pointer ${
                  isSelected
                    ? "bg-indigo-600 text-white shadow-xs"
                    : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50 hover:text-slate-900"
                }`}
              >
                <span>{cat}</span>
                <span
                  className={`rounded-full px-1.5 py-0.2 text-[10px] font-bold ${
                    isSelected
                      ? "bg-indigo-700/80 text-white"
                      : "bg-slate-100 text-slate-500"
                  }`}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      )}

      {/* Loading Skeletons */}
      {loading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="animate-pulse rounded-xl border border-slate-200 bg-white p-5 shadow-xs space-y-3"
            >
              <div className="flex items-center justify-between">
                <div className="h-5 bg-slate-200 rounded w-1/3"></div>
                <div className="h-5 bg-slate-200 rounded w-20"></div>
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

      {/* Memory List Content */}
      {!loading && isAvailable && (
        <>
          {allMemories.length === 0 ? (
            /* Total Empty Store */
            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center shadow-xs">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-indigo-50 text-indigo-600">
                <Brain className="h-6 w-6" />
              </div>
              <h3 className="mt-3 text-base font-semibold text-slate-900">
                No Memories Saved Yet
              </h3>
              <p className="mt-1 text-xs text-slate-500 max-w-md mx-auto">
                EchoMind hasn&apos;t saved any memories yet. As you talk with your assistant, important notes and commitments will appear here.
              </p>
            </div>
          ) : filteredMemories.length === 0 ? (
            /* Category Filter Returned 0 Results */
            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center shadow-xs">
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-slate-500">
                <FileQuestion className="h-5 w-5" />
              </div>
              <h3 className="mt-2 text-sm font-semibold text-slate-900">
                No Memories in &ldquo;{selectedCategory}&rdquo;
              </h3>
              <p className="mt-1 text-xs text-slate-500">
                You don&apos;t have any memories saved under {selectedCategory} yet.
              </p>
              <button
                type="button"
                onClick={() => setSelectedCategory("All")}
                className="mt-3 inline-flex items-center gap-1 rounded-lg bg-indigo-50 px-3 py-1.5 text-xs font-semibold text-indigo-700 hover:bg-indigo-100 transition-colors cursor-pointer"
              >
                View all memories ({allMemories.length})
              </button>
            </div>
          ) : (
            /* Memory Cards */
            <div className="space-y-4">
              {filteredMemories.map((memory) => {
                const hasSupersedes = memory.supersedes_id !== null && memory.supersedes_id !== undefined;
                const isDuplicate = memory.seen_count > 1;

                return (
                  <div
                    key={memory.id}
                    className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs transition-all hover:border-indigo-200 hover:shadow-xs"
                  >
                    {/* Header Row: Title, Category & Badges */}
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="rounded-md bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700 border border-slate-200">
                            {memory.category || "General"}
                          </span>
                          <h2 className="text-base font-semibold text-slate-900">
                            {memory.title}
                          </h2>
                        </div>
                      </div>

                      {/* Friendly Lifecycle Badges */}
                      <div className="flex flex-wrap items-center gap-1.5">
                        {hasSupersedes && (
                          <span className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-[10px] font-bold tracking-wide text-indigo-700 ring-1 ring-inset ring-indigo-600/20">
                            Updated
                          </span>
                        )}

                        {isDuplicate && (
                          <span className="rounded-full bg-amber-50 px-2.5 py-0.5 text-[10px] font-bold tracking-wide text-amber-800 ring-1 ring-inset ring-amber-600/20">
                            Mentioned {memory.seen_count} times
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Content Body */}
                    <p className="mt-3 text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {memory.content}
                    </p>

                    {/* Friendly Supersedes Informational Note */}
                    {hasSupersedes && (
                      <div className="mt-3 inline-flex items-center gap-1.5 rounded-md bg-indigo-50/60 border border-indigo-100 px-2.5 py-1 text-xs text-indigo-900">
                        <Repeat className="h-3.5 w-3.5 text-indigo-600 shrink-0" />
                        <span>Updated from an earlier memory</span>
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

                        <div className="flex items-center gap-1">
                          {memory.notification ? (
                            <>
                              <Bell className="h-3.5 w-3.5 text-indigo-600" />
                              <span className="text-indigo-700 font-medium">Reminder set</span>
                            </>
                          ) : (
                            <>
                              <BellOff className="h-3.5 w-3.5 text-slate-400" />
                              <span>No reminder set</span>
                            </>
                          )}
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
