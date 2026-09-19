import React from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import { Search, Sparkles, SlidersHorizontal, Info } from "lucide-react";

export default function SearchPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Semantic Search"
        description="Query memories using natural language powered by vector embeddings."
        badge="Semantic Retrieval"
      />

      <Card>
        <div className="space-y-4">
          <div className="relative">
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5">
              <Search className="h-4 w-4 text-slate-400" />
            </div>
            <input
              type="text"
              readOnly
              placeholder="Search concepts, questions, or topics (e.g. 'When is my project submission?')..."
              className="block w-full rounded-lg border border-slate-200 bg-slate-50 py-3 pr-4 pl-10 text-sm text-slate-700 placeholder-slate-400 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 cursor-not-allowed"
            />
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
            <div className="flex items-center gap-2">
              <SlidersHorizontal className="h-3.5 w-3.5" />
              <span>Similarity Threshold: 0.70</span>
              <span className="text-slate-300">•</span>
              <span>Model: Semantic Embeddings</span>
            </div>
            <button
              type="button"
              disabled
              className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white opacity-60 shadow-xs cursor-not-allowed"
            >
              <Sparkles className="h-3.5 w-3.5" />
              Query Memory Store
            </button>
          </div>
        </div>
      </Card>

      <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-indigo-50 text-indigo-600">
          <Search className="h-6 w-6" />
        </div>
        <h3 className="mt-3 text-sm font-semibold text-slate-900">
          Awaiting Search Integration
        </h3>
        <p className="mt-1 text-xs text-slate-500 max-w-md mx-auto">
          In the next phase, querying this interface will dispatch requests to the EchoMind Flask REST API, executing semantic retrieval against SQLite and embedding indexes.
        </p>
      </div>
    </div>
  );
}
