"use client";

import React, {
  useState,
} from "react";

import {
  PageHeader,
} from "@/components/common/PageHeader";

import {
  Card,
} from "@/components/common/Card";

import {
  formatDate,
  formatTime,
} from "@/lib/formatters";

import {
  ApiSearchResponse,
} from "@/types/api";

import {
  AlertTriangle,
  Calendar,
  Clock,
  FileQuestion,
  Search,
  Sparkles,
} from "lucide-react";


export default function SearchPage() {
  const [
    query,
    setQuery,
  ] = useState("");

  const [
    submittedQuery,
    setSubmittedQuery,
  ] = useState("");

  const [
    response,
    setResponse,
  ] =
    useState<ApiSearchResponse | null>(
      null,
    );

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    hasSearched,
    setHasSearched,
  ] = useState(false);


  const handleSearch =
    async (
      event?:
        React.FormEvent,
    ) => {
      if (event) {
        event.preventDefault();
      }

      const trimmed =
        query.trim();

      if (!trimmed) {
        setSubmittedQuery("");

        setResponse({
          available: true,
          results: [],
          query: "",
        });

        setHasSearched(true);

        return;
      }

      setLoading(true);
      setHasSearched(true);
      setSubmittedQuery(trimmed);

      try {
        const result =
          await fetch(
            `/api/memories/search?q=${encodeURIComponent(trimmed)}`,
            {
              cache:
                "no-store",
            },
          );

        const data =
          (await result.json()) as ApiSearchResponse;

        setResponse(data);

      } catch (
        error: unknown
      ) {
        setResponse({
          available: false,

          error:
            error instanceof Error
              ? error.message
              : "Search request failed.",

          query:
            trimmed,
        });

      } finally {
        setLoading(false);
      }
    };


  const results =
    response?.available &&
    response.results
      ? response.results
      : [];

  const isAvailable =
    response?.available !==
    false;


  return (
    <div className="space-y-6">

      <PageHeader
        title="Find a Memory"
        description="Ask EchoMind naturally about information you previously mentioned."
        badge={
          loading
            ? "Searching..."
            : hasSearched &&
              isAvailable
            ? `${results.length} Result${
                results.length === 1
                  ? ""
                  : "s"
              }`
            : undefined
        }
      />


      <Card>

        <form
          onSubmit={
            handleSearch
          }
          className="space-y-4"
        >

          <div className="relative">

            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4">

              <Search className="h-5 w-5 text-slate-400" />

            </div>


            <input
              type="text"
              value={
                query
              }
              onChange={(
                event,
              ) =>
                setQuery(
                  event.target.value,
                )
              }
              placeholder="What do I have planned for Monday?"
              className="block w-full rounded-xl border border-slate-200 bg-white py-3.5 pl-11 pr-28 text-sm text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-indigo-400 focus:ring-4 focus:ring-indigo-100"
            />


            <div className="absolute inset-y-1.5 right-1.5 flex items-center">

              <button
                type="submit"
                disabled={
                  loading
                }
                className="inline-flex h-full items-center gap-1.5 rounded-lg bg-indigo-600 px-4 text-xs font-bold text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
              >

                <Sparkles className="h-3.5 w-3.5" />

                {loading
                  ? "Searching..."
                  : "Search"}

              </button>

            </div>

          </div>


          <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">

            <span>
              Search naturally using names, events, tasks or details you remember.
            </span>

            <span className="hidden sm:inline">
              Press{" "}
              <kbd className="rounded-md border border-slate-200 bg-slate-50 px-1.5 py-0.5 font-mono text-[10px] text-slate-600">
                Enter
              </kbd>
            </span>

          </div>

        </form>

      </Card>


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
                  Start the Python EchoMind backend and try your search again.
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

                <div className="flex items-center justify-between">

                  <div className="h-5 w-1/3 rounded bg-slate-200" />

                  <div className="h-5 w-24 rounded bg-slate-200" />

                </div>

                <div className="mt-4 h-4 w-full rounded bg-slate-200" />

                <div className="mt-2 h-4 w-3/4 rounded bg-slate-200" />

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
        !hasSearched && (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white/80 p-12 text-center shadow-sm">

            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">

              <Search className="h-6 w-6" />

            </div>

            <h3 className="mt-4 text-base font-bold text-slate-950">
              Search your memories
            </h3>

            <p className="mx-auto mt-1 max-w-md text-xs leading-relaxed text-slate-500">
              Ask about appointments, people, commitments, tasks or anything EchoMind previously stored.
            </p>

          </div>
        )}


      {!loading &&
        isAvailable &&
        hasSearched &&
        results.length ===
          0 && (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center shadow-sm">

            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-500">

              <FileQuestion className="h-6 w-6" />

            </div>

            <h3 className="mt-4 text-base font-bold text-slate-950">
              No matching memories
            </h3>

            <p className="mx-auto mt-1 max-w-md text-xs leading-relaxed text-slate-500">

              {submittedQuery ? (
                <>
                  EchoMind could not find a memory matching{" "}
                  <span className="font-semibold text-slate-700">
                    &ldquo;{submittedQuery}&rdquo;
                  </span>
                  . Try using different wording.
                </>
              ) : (
                "Enter a question to search your memories."
              )}

            </p>

          </div>
        )}


      {!loading &&
        isAvailable &&
        hasSearched &&
        results.length >
          0 && (
          <div className="space-y-4">

            <div className="px-1 text-xs text-slate-500">

              Found{" "}

              <strong className="text-slate-800">
                {results.length}
              </strong>{" "}

              relevant{" "}

              {results.length ===
              1
                ? "memory"
                : "memories"}{" "}

              for{" "}

              <span className="font-medium text-slate-700">
                &ldquo;{submittedQuery}&rdquo;
              </span>

            </div>


            {results.map(
              (
                result,
              ) => {

                const scorePercent =
                  typeof result.score ===
                  "number"
                    ? Math.round(
                        result.score *
                          100,
                      )
                    : null;

                const hasDate =
                  Boolean(
                    result.date?.trim(),
                  );

                const hasTime =
                  Boolean(
                    result.time?.trim(),
                  );


                return (
                  <div
                    key={
                      result.id
                    }
                    className="rounded-2xl border border-slate-200/80 bg-white/90 p-5 shadow-[0_8px_30px_rgba(15,23,42,0.04)] transition hover:border-indigo-200 hover:shadow-md sm:p-6"
                  >

                    <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">

                      <div className="min-w-0">

                        <div className="flex flex-wrap items-center gap-2">

                          <span className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-[10px] font-bold text-slate-600">
                            {result.category ||
                              "General"}
                          </span>

                          <h2 className="text-base font-bold text-slate-950">
                            {result.title}
                          </h2>

                        </div>

                      </div>


                      {scorePercent !==
                        null && (
                        <div className="inline-flex w-fit items-center gap-1.5 rounded-full bg-indigo-50 px-3 py-1 text-[10px] font-bold text-indigo-700 ring-1 ring-indigo-600/15">

                          <Sparkles className="h-3.5 w-3.5" />

                          {scorePercent}% match

                        </div>
                      )}

                    </div>


                    <p className="mt-4 whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
                      {result.content}
                    </p>


                    <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-slate-100 pt-4 text-xs text-slate-500">

                      <span className="inline-flex items-center gap-1.5">

                        <Calendar className="h-3.5 w-3.5 text-slate-400" />

                        {hasDate
                          ? formatDate(
                              result.date,
                            )
                          : "No date set"}

                      </span>


                      <span className="inline-flex items-center gap-1.5">

                        <Clock className="h-3.5 w-3.5 text-slate-400" />

                        {hasTime
                          ? formatTime(
                              result.time,
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