import React from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import { ShieldCheck, Lock, EyeOff, ShieldAlert, Cpu } from "lucide-react";

export default function PrivacyPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Privacy Gateway"
        description="Semantic privacy classifier, confidentiality rules, and local guardrails."
        badge="Gateway Guarded"
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Card
          title="Classifier Configuration"
          subtitle="Real-time evaluation before memory persistence"
        >
          <div className="space-y-4">
            <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 p-3">
              <div className="flex items-center gap-3">
                <div className="rounded-md bg-emerald-100 p-1.5 text-emerald-700">
                  <Lock className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-900">
                    Sensitive Data Detection
                  </p>
                  <p className="text-xs text-slate-500">
                    Filters passwords, credentials, and financial entities
                  </p>
                </div>
              </div>
              <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800">
                Active
              </span>
            </div>

            <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 p-3">
              <div className="flex items-center gap-3">
                <div className="rounded-md bg-indigo-100 p-1.5 text-indigo-700">
                  <EyeOff className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-900">
                    Semantic Privacy Filter
                  </p>
                  <p className="text-xs text-slate-500">
                    Classifies conversational sensitivity prior to LLM/embedding
                  </p>
                </div>
              </div>
              <span className="rounded-full bg-indigo-100 px-2.5 py-0.5 text-xs font-semibold text-indigo-800">
                Active
              </span>
            </div>
          </div>
        </Card>

        <Card
          title="Security Boundaries"
          subtitle="Decoupled Architecture Guarantees"
        >
          <div className="space-y-3 text-xs text-slate-600">
            <div className="flex items-start gap-2.5">
              <ShieldCheck className="h-4 w-4 shrink-0 text-emerald-600 mt-0.5" />
              <div>
                <p className="font-semibold text-slate-800">No Browser Database Access</p>
                <p className="text-slate-500">
                  The Next.js frontend has zero direct connection to SQLite. All interactions route through controlled Flask REST endpoints.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-2.5">
              <ShieldCheck className="h-4 w-4 shrink-0 text-emerald-600 mt-0.5" />
              <div>
                <p className="font-semibold text-slate-800">Zero Secret Exposure</p>
                <p className="text-slate-500">
                  Gemini API keys, backend environment variables, and speech recognition weights remain strictly isolated on the backend.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-2.5">
              <ShieldCheck className="h-4 w-4 shrink-0 text-emerald-600 mt-0.5" />
              <div>
                <p className="font-semibold text-slate-800">Dual Frontend Compatibility</p>
                <p className="text-slate-500">
                  The original Flask HTML templates in <code className="font-mono bg-slate-100 px-1 py-0.5 rounded text-slate-800">web/</code> remain intact and fully operational.
                </p>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
