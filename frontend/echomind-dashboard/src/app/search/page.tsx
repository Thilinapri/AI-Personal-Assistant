"use client";

import React, { useState } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import { ApiSearchResponse, MemorySearchResult } from "@/types/api";
import {
  Search,
  Sparkles,
  AlertTriangle,
  Calendar,
  Clock,
  Info,
  Terminal,
  FileQuestion,
  Tag,
  Percent,
} from "lucide-react";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [response, setResponse] = useState<ApiSearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    const trimmed = query.trim();
    if (!trimmed) {
      setSubmittedQuery("");
      setResponse({ available: true, results: [], query: "" });
      setHasSearched(true);
      return;
    }

    setLoading(true);
    setHasSearched(true);
    setSubmittedQuery(trimmed);

    try {
      const res = await fetch(
        `/api/memories/search?q=${encodeURIComponent(trimmed)}`,
        { cache: "no-store" }
      );
      const data: ApiSearchResponse = await res.json();
      setResponse(data);
    } catch (err: unknown) {
      setResponse({
        available: false,
        error: err instanceof Error ? err.message : "Search request failed",
        query: trimmed,
      });
    } finally {
      setLoading(false);
    }
  };

  const results = response?.available && response.results ? response.results : [];
  const isAvailable = response?.available !== false;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Semantic Search"
        description="Natural-language memory recall powered by vector embeddings and cosine similarity."
        badge={
          loading
            ? "Searching..."
            : hasSearched
            ? isAvailable
              ? `${results.length} Match${results.length === 1 ? "" : "es"}`
              : "Backend Offline"
            : "Semantic Retrieval"
        }
      />

      {/* Search Input Form */}
      <Card>
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="relative">
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5">
              <Search className="h-5 w-5 text-slate-400" />
            </div>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a question or enter a concept (e.g. 'What reminder test do I have?')..."
              className="block w-full rounded-lg border border-slate-300 bg-white py-3 pr-24 pl-11 text-sm text-slate-900 placeholder-slate-400 shadow-xs focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
            <div className="absolute inset-y-1.5 right-1.5 flex items-center">
              <button
                type="submit"
                disabled={loading}
                className="inline-flex h-full items-center gap-1.5 rounded-md bg-indigo-600 px-4 text-xs font-semibold text-white shadow-xs hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 transition-colors cursor-pointer"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>{loading ? "Searching..." : "Search"}</span>
              </button>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
            <span>Press <kbd className="rounded border border-slate-200 bg-slate-100 px-1.5 py-0.5 font-mono text-[10px] text-slate-600">Enter</kbd> to execute natural-language search</span>
            <span className="text-[11px] text-slate-400">Queries are evaluated against semantic embeddings</span>
          </div>
        </form>
      </Card>

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
                  The Next.js API proxy cannot reach the EchoMind Flask API for semantic retrieval.
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

      {/* Loading Skeleton State */}
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
              <div className="h-4 bg-slate-200 rounded w-3/4"></div>
              <div className="pt-2 border-t border-slate-100 flex gap-4">
                <div className="h-3 bg-slate-200 rounded w-24"></div>
                <div className="h-3 bg-slate-200 rounded w-24"></div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Initial State (Before Searching) */}
      {!loading && isAvailable && !hasSearched && (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center shadow-xs">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-indigo-50 text-indigo-600">
            <Search className="h-6 w-6" />
          </div>
          <h3 className="mt-3 text-base font-semibold text-slate-900">
            Semantic Memory Recall
          </h3>
          <p className="mt-1 text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
            Type any question, topic, or conversational fragment into the box above. EchoMind calculates cosine similarity between your query vector and stored memory embeddings.
          </p>
        </div>
      )}

      {/* No Matches State */}
      {!loading && isAvailable && hasSearched && results.length === 0 && (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center shadow-xs">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-500">
            <FileQuestion className="h-6 w-6" />
          </div>
          <h3 className="mt-3 text-base font-semibold text-slate-900">
            No Semantically Matching Memories Found
          </h3>
          <p className="mt-1 text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
            {submittedQuery ? (
              <>
                No active memories matched your query &ldquo;<span className="font-medium text-slate-700">{submittedQuery}</span>&rdquo; above the backend similarity threshold.
              </>
            ) : (
              "Please enter a search query to retrieve relevant memories."
            )}
          </p>
        </div>
      )}

      {/* Successful Results State */}
      {!loading && isAvailable && hasSearched && results.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-500 px-1">
            <span>
              Found <strong className="text-slate-800">{results.length}</strong> matching memor{results.length === 1 ? "y" : "ies"} for &ldquo;<span className="text-slate-700">{submittedQuery}</span>&rdquo;
            </span>
            <span className="text-slate-400">Ranked by similarity score</span>
          </div>

          <div className="space-y-4">
            {results.map((result) => {
              // Convert numeric similarity score (e.g. 0.555) to user-friendly percentage (e.g. 56% match)
              const scorePercent = typeof result.score === "number"
                ? Math.round(result.score * 100)
                : null;

              return (
                <div
                  key={result.id}
                  className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs transition-all hover:border-indigo-200 hover:shadow-sm"
                >
                  {/* Card Header: Category, Title & Relevance Score */}
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-700 border border-slate-200">
                          {result.category || "General"}
                        </span>
                        <h2 className="text-base font-semibold text-slate-900">
                          {result.title}
                        </h2>
                      </div>
                    </div>

                    {/* Numeric Similarity Score displayed as user-friendly percentage */}
                    {scorePercent !== null && (
                      <div
                        className="inline-flex items-center gap-1.5 rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700 ring-1 ring-inset ring-indigo-600/20"
                        title={`Cosine similarity score: ${result.score.toFixed(4)}`}
                      >
                        <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
                        <span>{scorePercent}% match</span>
                        <span className="text-[10px] text-indigo-400 font-mono">
                          ({result.score.toFixed(3)})
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Content Body */}
                  <p className="mt-3 text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                    {result.content}
                  </p>

                  {/* Metadata Footer */}
                  <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-3 text-xs text-slate-500">
                    <div className="flex flex-wrap items-center gap-4">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3.5 w-3.5 text-slate-400" />
                        <span>{result.date && result.date.trim() ? result.date : "No date set"}</span>
                      </div>

                      <div className="flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5 text-slate-400" />
                        <span>{result.time && result.time.trim() ? result.time : "No time set"}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 text-[11px] text-slate-400">
                      <span className="font-mono">ID #{result.id}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Semantic Retrieval System Note */}
      <div className="rounded-xl border border-indigo-100 bg-indigo-50/50 p-4 text-xs text-indigo-900 shadow-xs">
        <div className="flex items-start gap-2.5">
          <Info className="h-4 w-4 shrink-0 text-indigo-600 mt-0.5" />
          <div className="space-y-1">
            <span className="font-semibold text-indigo-950">
              EchoMind Semantic Retrieval Engine
            </span>
            <p className="text-indigo-800 leading-relaxed text-[11px] sm:text-xs">
              Results are retrieved using EchoMind semantic vector embeddings and cosine similarity. The Flask backend compares your natural-language query against stored memory embeddings and returns only active memories meeting the pre-configured similarity threshold.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
