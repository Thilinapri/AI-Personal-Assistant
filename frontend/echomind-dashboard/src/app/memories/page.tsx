import React from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import { Brain, Trash2, RefreshCw, AlertCircle, Clock } from "lucide-react";

export default function MemoriesPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Memories"
        description="View, curate, and manage consolidated long-term episodic memories."
        badge="Module 01"
        actions={
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 opacity-60 shadow-xs cursor-not-allowed"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Refresh
            </button>
            <button
              type="button"
              disabled
              className="inline-flex items-center gap-1.5 rounded-lg bg-rose-600 px-3 py-2 text-xs font-semibold text-white opacity-60 shadow-xs cursor-not-allowed"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Clear All Memories
            </button>
          </div>
        }
      />

      <div className="rounded-xl border border-amber-100 bg-amber-50/60 p-4 text-xs text-amber-800 flex items-start gap-2.5">
        <AlertCircle className="h-4 w-4 shrink-0 text-amber-600 mt-0.5" />
        <div>
          <span className="font-semibold text-amber-900">API Integration Notice: </span>
          This view will fetch and clear memory records via the Flask REST API endpoints (<code className="font-mono bg-amber-100/80 px-1 py-0.5 rounded text-amber-900">GET /api/memories</code> and <code className="font-mono bg-amber-100/80 px-1 py-0.5 rounded text-amber-900">POST /api/memories/clear</code>) once backend endpoints are connected in the subsequent step.
        </div>
      </div>

      <Card
        title="Memory Store"
        subtitle="Consolidated memory items extracted from ambient speech"
      >
        <div className="space-y-3">
          {/* Mock placeholder memory cards */}
          <div className="rounded-lg border border-slate-200 bg-slate-50/50 p-4 transition-colors">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-start gap-3">
                <div className="mt-0.5 rounded-md bg-indigo-100 p-1.5 text-indigo-700">
                  <Brain className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-900">
                    Project discussion on EchoMind architecture &amp; requirements
                  </p>
                  <p className="mt-1 text-xs text-slate-500 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    Placeholder Timestamp • Source: Transcribed Audio
                  </p>
                </div>
              </div>
              <span className="rounded bg-slate-200 px-2 py-0.5 text-[10px] font-semibold text-slate-700">
                Sample Record
              </span>
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-slate-50/50 p-4 transition-colors">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-start gap-3">
                <div className="mt-0.5 rounded-md bg-indigo-100 p-1.5 text-indigo-700">
                  <Brain className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-900">
                    Meeting scheduled with academic advisor on Thursday at 2:00 PM
                  </p>
                  <p className="mt-1 text-xs text-slate-500 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    Placeholder Timestamp • Source: Transcribed Audio
                  </p>
                </div>
              </div>
              <span className="rounded bg-slate-200 px-2 py-0.5 text-[10px] font-semibold text-slate-700">
                Sample Record
              </span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
