import React from "react";
import Link from "next/link";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import {
  Mic,
  Brain,
  Search,
  Bell,
  History,
  ShieldCheck,
  Server,
  ArrowRight,
  Database,
  Info,
} from "lucide-react";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="System overview, speech capture status, and memory metrics."
        badge="System Ready"
      />

      {/* Architecture overview banner */}
      <div className="rounded-xl border border-indigo-100 bg-indigo-50/50 p-4 sm:p-5">
        <div className="flex items-start gap-3">
          <Info className="mt-0.5 h-5 w-5 shrink-0 text-indigo-600" />
          <div className="space-y-1 text-sm text-indigo-950">
            <p className="font-semibold text-indigo-900">
              EchoMind Architecture &amp; Next.js Frontend Shell
            </p>
            <p className="text-xs leading-relaxed text-indigo-800 sm:text-sm">
              This Next.js application shell runs in decoupled mode alongside the existing Flask dashboard. In the next phase, live state and controls will be wired via the EchoMind Flask REST API without direct SQLite or backend secret exposure.
            </p>
          </div>
        </div>
      </div>

      {/* Top metrics / status cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card
          title="Microphone &amp; STT"
          subtitle="Faster-Whisper audio ingestion"
        >
          <div className="flex items-center justify-between pt-2">
            <div>
              <p className="text-xs font-medium text-slate-500">Audio Capture</p>
              <p className="text-lg font-bold text-slate-900">Idle / Ready</p>
            </div>
            <div className="rounded-full bg-slate-100 p-2.5 text-slate-600">
              <Mic className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-4 border-t border-slate-100 pt-3">
            <span className="inline-flex items-center gap-1.5 text-xs text-slate-500">
              <span className="h-2 w-2 rounded-full bg-amber-400"></span>
              Awaiting Flask API connection
            </span>
          </div>
        </Card>

        <Card
          title="Memory Manager"
          subtitle="Episodic semantic storage"
        >
          <div className="flex items-center justify-between pt-2">
            <div>
              <p className="text-xs font-medium text-slate-500">Stored Memories</p>
              <p className="text-lg font-bold text-slate-900">-- items</p>
            </div>
            <div className="rounded-full bg-indigo-50 p-2.5 text-indigo-600">
              <Brain className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-4 border-t border-slate-100 pt-3">
            <Link
              href="/memories"
              className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-700"
            >
              View memory catalog <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </Card>

        <Card
          title="Privacy Gateway"
          subtitle="Semantic classifier &amp; guardrails"
        >
          <div className="flex items-center justify-between pt-2">
            <div>
              <p className="text-xs font-medium text-slate-500">Protection Layer</p>
              <p className="text-lg font-bold text-emerald-600">Active</p>
            </div>
            <div className="rounded-full bg-emerald-50 p-2.5 text-emerald-600">
              <ShieldCheck className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-4 border-t border-slate-100 pt-3">
            <Link
              href="/privacy"
              className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 hover:text-emerald-700"
            >
              Check privacy rules <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </Card>
      </div>

      {/* Navigation Quick Access Grid */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-slate-900">
          Application Modules
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Link
            href="/memories"
            className="group rounded-xl border border-slate-200 bg-white p-5 transition-all hover:border-indigo-200 hover:shadow-sm"
          >
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-indigo-50 p-2 text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                <Brain className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Memories</h3>
                <p className="text-xs text-slate-500">Manage consolidated facts</p>
              </div>
            </div>
          </Link>

          <Link
            href="/search"
            className="group rounded-xl border border-slate-200 bg-white p-5 transition-all hover:border-indigo-200 hover:shadow-sm"
          >
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-sky-50 p-2 text-sky-600 group-hover:bg-sky-600 group-hover:text-white transition-colors">
                <Search className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Semantic Search</h3>
                <p className="text-xs text-slate-500">Natural language memory recall</p>
              </div>
            </div>
          </Link>

          <Link
            href="/reminders"
            className="group rounded-xl border border-slate-200 bg-white p-5 transition-all hover:border-indigo-200 hover:shadow-sm"
          >
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-amber-50 p-2 text-amber-600 group-hover:bg-amber-600 group-hover:text-white transition-colors">
                <Bell className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Reminders</h3>
                <p className="text-xs text-slate-500">Track scheduled commitments</p>
              </div>
            </div>
          </Link>

          <Link
            href="/history"
            className="group rounded-xl border border-slate-200 bg-white p-5 transition-all hover:border-indigo-200 hover:shadow-sm"
          >
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-purple-50 p-2 text-purple-600 group-hover:bg-purple-600 group-hover:text-white transition-colors">
                <History className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Memory History</h3>
                <p className="text-xs text-slate-500">Inspect transcription buffers</p>
              </div>
            </div>
          </Link>

          <Link
            href="/privacy"
            className="group rounded-xl border border-slate-200 bg-white p-5 transition-all hover:border-indigo-200 hover:shadow-sm"
          >
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-emerald-50 p-2 text-emerald-600 group-hover:bg-emerald-600 group-hover:text-white transition-colors">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Privacy Gateway</h3>
                <p className="text-xs text-slate-500">Semantic classifier settings</p>
              </div>
            </div>
          </Link>

          <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50/50 p-5">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-slate-100 p-2 text-slate-500">
                <Database className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-700">Storage Engine</h3>
                <p className="text-xs text-slate-500">SQLite + FAISS (via Flask)</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
