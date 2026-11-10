"use client";

import React, {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  PageHeader,
} from "@/components/common/PageHeader";

import {
  formatDate,
  formatTime,
} from "@/lib/formatters";

import {
  ApiMemoryHistoryResponse,
} from "@/types/api";

import {
  AlertTriangle,
  Archive,
  Calendar,
  Clock,
  Info,
  RefreshCw,
  Repeat,
} from "lucide-react";


export default function HistoryPage() {
  const [
    response,
    setResponse,
  ] =
    useState<ApiMemoryHistoryResponse | null>(
      null,
    );

  const [
    loading,
    setLoading,
  ] =
    useState(true);


  const fetchHistory =
    useCallback(
      async () => {
        setLoading(true);

        try {
          const result =
            await fetch(
              "/api/memories/history",
              {
                cache:
                  "no-store",
              },
            );

          const data =
            (await result.json()) as ApiMemoryHistoryResponse;

          setResponse(data);

        } catch (
          error: unknown
        ) {
          setResponse({
            available:
              false,

            error:
              error instanceof Error
                ? error.message
                : "Failed to load memory history.",
          });

        } finally {
          setLoading(false);
        }
      },
      [],
    );


  useEffect(
    () => {
      fetchHistory();
    },
    [
      fetchHistory,
    ],
  );


  const historyMemories =
    useMemo(
      () => {
        if (
          !response?.available ||
          !response.memories
        ) {
          return [];
        }

        return [
          ...response.memories,
        ].sort(
          (
            first,
            second,
          ) =>
            second.id -
            first.id,
        );
      },
      [
        response,
      ],
    );


  const isAvailable =
    response?.available ===
    true;


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
            onClick={
              fetchHistory
            }
            disabled={
              loading
            }
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm transition hover:border-purple-200 hover:bg-purple-50 hover:text-purple-700 disabled:opacity-50"
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


      <div className="rounded-2xl border border-purple-100 bg-purple-50/60 p-4 text-xs text-purple-950 shadow-sm">

        <div className="flex items-start gap-3">

          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-purple-100 text-purple-600">
            <Info className="h-4 w-4" />
          </div>

          <div>
            <p className="font-bold text-purple-950">
              Memory Archive
            </p>

            <p className="mt-1 leading-relaxed text-purple-800">
              This section keeps earlier versions of memories when EchoMind learns newer or corrected information.
            </p>
          </div>

        </div>

      </div>


      {!loading &&
        !isAvailable && (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-amber-950 shadow-sm">

            <div className="flex items-start gap-3">

              <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />

              <div>
                <h3 className="text-sm font-bold text-amber-950">
                  EchoMind is unavailable
                </h3>

                <p className="mt-1 text-xs leading-relaxed text-amber-800">
                  Start the Python EchoMind backend and refresh this page.
                </p>
              </div>

            </div>

          </div>
        )}


      {loading && (
        <div className="space-y-4">

          {[1, 2].map(
            (
              value,
            ) => (
              <div
                key={
                  value
                }
                className="animate-pulse rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
              >
                <div className="h-5 w-1/3 rounded bg-slate-200" />

                <div className="mt-4 h-4 w-full rounded bg-slate-200" />

                <div className="mt-2 h-4 w-2/3 rounded bg-slate-200" />

                <div className="mt-4 flex gap-4 border-t border-slate-100 pt-3">
                  <div className="h-3 w-24 rounded bg-slate-200" />
                  <div className="h-3 w-24 rounded bg-slate-200" />
                </div>
              </div>
            ),
          )}

        </div>
      )}


      {!loading &&
        isAvailable &&
        historyMemories.length ===
          0 && (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white/80 p-12 text-center shadow-sm">

            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-purple-50 text-purple-600">
              <Archive className="h-6 w-6" />
            </div>

            <h3 className="mt-4 text-base font-bold text-slate-950">
              No replaced memories
            </h3>

            <p className="mx-auto mt-1 max-w-md text-xs leading-relaxed text-slate-500">
              Earlier versions will appear here when EchoMind updates stored information with newer details.
            </p>

          </div>
        )}


      {!loading &&
        isAvailable &&
        historyMemories.length >
          0 && (
          <div className="space-y-4">

            {historyMemories.map(
              (
                memory,
              ) => {
                const duplicate =
                  memory.seen_count >
                  1;

                const hasSupersedes =
                  memory.supersedes_id !==
                    null &&
                  memory.supersedes_id !==
                    undefined;

                const hasDate =
                  Boolean(
                    memory.date?.trim(),
                  );

                const hasTime =
                  Boolean(
                    memory.time?.trim(),
                  );


                return (
                  <div
                    key={
                      memory.id
                    }
                    className="rounded-2xl border border-slate-200/80 bg-white/90 p-5 shadow-[0_8px_30px_rgba(15,23,42,0.04)] transition hover:border-purple-200 hover:shadow-md sm:p-6"
                  >

                    <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">

                      <div className="min-w-0">

                        <div className="flex flex-wrap items-center gap-2">

                          <span className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-[10px] font-bold text-slate-600">
                            {memory.category ||
                              "General"}
                          </span>

                          <h2 className="text-base font-bold text-slate-950">
                            {memory.title}
                          </h2>

                        </div>

                      </div>


                      <div className="flex flex-wrap items-center gap-1.5">

                        <span className="rounded-full bg-purple-50 px-2.5 py-1 text-[10px] font-bold text-purple-700 ring-1 ring-purple-600/15">
                          REPLACED
                        </span>


                        {duplicate && (
                          <span className="rounded-full bg-amber-50 px-2.5 py-1 text-[10px] font-bold text-amber-700 ring-1 ring-amber-600/15">
                            Mentioned {memory.seen_count} times
                          </span>
                        )}

                      </div>

                    </div>


                    <p className="mt-4 whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
                      {memory.content}
                    </p>


                    <p className="mt-2 text-xs italic text-slate-500">
                      This memory was replaced by newer information.
                    </p>


                    {hasSupersedes && (
                      <div className="mt-3 inline-flex items-center gap-2 rounded-xl border border-purple-100 bg-purple-50/70 px-3 py-2 text-xs text-purple-900">

                        <Repeat className="h-3.5 w-3.5 shrink-0 text-purple-600" />

                        <span>
                          This version originally updated an earlier memory.
                        </span>

                      </div>
                    )}


                    <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-slate-100 pt-4 text-xs text-slate-500">

                      <span className="inline-flex items-center gap-1.5">

                        <Calendar className="h-3.5 w-3.5 text-slate-400" />

                        {hasDate
                          ? formatDate(
                              memory.date,
                            )
                          : "No date set"}

                      </span>


                      <span className="inline-flex items-center gap-1.5">

                        <Clock className="h-3.5 w-3.5 text-slate-400" />

                        {hasTime
                          ? formatTime(
                              memory.time,
                            )
                          : "No time set"}

                      </span>

                    </div>

                  </div>
                );
              },
            )}

          </div>
        )}

    </div>
  );
}