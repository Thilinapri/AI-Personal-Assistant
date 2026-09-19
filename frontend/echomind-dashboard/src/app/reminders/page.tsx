import React from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import { Bell, Calendar, Clock, Plus, CheckCircle2 } from "lucide-react";

export default function RemindersPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Reminders"
        description="Automated commitments and task alerts detected by Reminder Manager."
        badge="Manager Active"
        actions={
          <button
            type="button"
            disabled
            className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-2 text-xs font-semibold text-white opacity-60 shadow-xs cursor-not-allowed"
          >
            <Plus className="h-3.5 w-3.5" />
            New Reminder
          </button>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Card
          title="Active Reminders"
          subtitle="Scheduled events parsed from speech &amp; assistant logs"
        >
          <div className="space-y-3">
            <div className="flex items-start justify-between rounded-lg border border-slate-200 bg-slate-50/50 p-3.5">
              <div className="flex items-start gap-3">
                <div className="mt-0.5 rounded-md bg-amber-100 p-1.5 text-amber-700">
                  <Bell className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-900">
                    Review EchoMind test results with group
                  </p>
                  <p className="mt-1 flex items-center gap-2 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" /> Today
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" /> 5:00 PM
                    </span>
                  </p>
                </div>
              </div>
              <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-medium text-amber-800">
                Pending
              </span>
            </div>

            <div className="flex items-start justify-between rounded-lg border border-slate-200 bg-slate-50/50 p-3.5">
              <div className="flex items-start gap-3">
                <div className="mt-0.5 rounded-md bg-emerald-100 p-1.5 text-emerald-700">
                  <CheckCircle2 className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-900 line-through text-slate-500">
                    Complete transcript buffer sanity check
                  </p>
                  <p className="mt-1 text-xs text-slate-400">
                    Completed • Handled by Reminder Manager
                  </p>
                </div>
              </div>
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600">
                Resolved
              </span>
            </div>
          </div>
        </Card>

        <Card
          title="Reminder Engine Info"
          subtitle="EchoMind Backend Pipeline"
        >
          <div className="space-y-3 text-xs text-slate-600">
            <p>
              EchoMind analyzes conversational buffers to extract temporal cues, scheduled commitments, and deadlines.
            </p>
            <div className="rounded-lg bg-slate-50 p-3 space-y-1.5 border border-slate-200">
              <p className="font-semibold text-slate-800">Pipeline Stages:</p>
              <ul className="list-disc list-inside space-y-1 text-slate-600">
                <li>Faster-Whisper transcription</li>
                <li>Privacy Gateway validation</li>
                <li>Reminder extraction &amp; timestamp resolution</li>
                <li>SQLite persistence</li>
              </ul>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
