import React from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import { History, AudioLines, FileText, CheckCircle } from "lucide-react";

export default function HistoryPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Memory History"
        description="Chronological log of speech captures, transcript buffering, and memory consolidations."
        badge="Audit Trail"
      />

      <Card
        title="Recent Buffer Events"
        subtitle="Live transcript events captured by the audio listener"
      >
        <div className="relative border-l-2 border-slate-200 ml-3 space-y-6 py-2">
          <div className="relative pl-6">
            <div className="absolute -left-[9px] top-1.5 h-4 w-4 rounded-full border-2 border-white bg-indigo-600"></div>
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span className="flex items-center gap-1.5 font-medium text-slate-700">
                  <AudioLines className="h-3.5 w-3.5 text-indigo-600" />
                  Audio Chunk Transcribed
                </span>
                <span>Buffer #104</span>
              </div>
              <p className="mt-2 text-sm text-slate-800">
                &ldquo;Remember to submit the software design documentation by Friday afternoon.&rdquo;
              </p>
              <div className="mt-3 flex items-center gap-2">
                <span className="rounded bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700">
                  Privacy Passed
                </span>
                <span className="rounded bg-indigo-50 px-2 py-0.5 text-[10px] font-semibold text-indigo-700">
                  Memory Created
                </span>
              </div>
            </div>
          </div>

          <div className="relative pl-6">
            <div className="absolute -left-[9px] top-1.5 h-4 w-4 rounded-full border-2 border-white bg-slate-400"></div>
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span className="flex items-center gap-1.5 font-medium text-slate-700">
                  <FileText className="h-3.5 w-3.5 text-slate-500" />
                  Transcript Buffer Flushed
                </span>
                <span>Buffer #103</span>
              </div>
              <p className="mt-2 text-sm text-slate-800">
                &ldquo;Testing microphone levels and speech recognition latency for university presentation.&rdquo;
              </p>
              <div className="mt-3 flex items-center gap-2">
                <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
                  Informational
                </span>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
