"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import {
  ApiCancelReminderResponse,
  ApiRemindersResponse,
  Reminder,
  ReminderStatusFilter,
} from "@/types/api";
import {
  Bell,
  RefreshCw,
  AlertTriangle,
  Calendar,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Terminal,
  FileQuestion,
  Tag,
  Loader2,
  Trash2,
  HelpCircle,
  Check,
  X,
} from "lucide-react";

const STATUS_FILTERS: ReminderStatusFilter[] = [
  "All",
  "Pending",
  "Triggered",
  "Cancelled",
];

export default function RemindersPage() {
  const [response, setResponse] = useState<ApiRemindersResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedStatus, setSelectedStatus] = useState<ReminderStatusFilter>("All");
  const [cancellingId, setCancellingId] = useState<number | null>(null);
  const [confirmCancelId, setConfirmCancelId] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const fetchReminders = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/reminders", { cache: "no-store" });
      const data: ApiRemindersResponse = await res.json();
      setResponse(data);
    } catch (err: unknown) {
      setResponse({
        available: false,
        error: err instanceof Error ? err.message : "Failed to load reminders",
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchReminders();
  }, [fetchReminders]);

  const allReminders = useMemo(() => {
    return response?.available && response.reminders ? response.reminders : [];
  }, [response]);

  // Compute status counts for filter pills
  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = { All: allReminders.length };
    for (const st of ["Pending", "Triggered", "Cancelled"] as const) {
      counts[st] = allReminders.filter(
        (r) => r.status.trim().toLowerCase() === st.toLowerCase()
      ).length;
    }
    return counts;
  }, [allReminders]);

  // Filter and sort reminders
  const filteredAndSortedReminders = useMemo(() => {
    let list = [...allReminders];

    if (selectedStatus !== "All") {
      list = list.filter(
        (r) => r.status.trim().toLowerCase() === selectedStatus.toLowerCase()
      );
    }

    // Sort: Pending reminders by reminder_time ascending (earliest first)
    list.sort((a, b) => {
      const aPending = a.status.trim().toLowerCase() === "pending";
      const bPending = b.status.trim().toLowerCase() === "pending";

      // If both pending, sort by reminder_time ascending
      if (aPending && bPending) {
        return (a.reminder_time || "").localeCompare(b.reminder_time || "");
      }

      // If only one is pending, pending comes first
      if (aPending !== bPending) {
        return aPending ? -1 : 1;
      }

      // Otherwise sort by created_at or reminder_time descending (newest first)
      return (b.created_at || b.reminder_time || "").localeCompare(
        a.created_at || a.reminder_time || ""
      );
    });

    return list;
  }, [allReminders, selectedStatus]);

  // Handle Cancellation Flow
  const handleConfirmCancel = async (id: number) => {
    setCancellingId(id);
    setConfirmCancelId(null);
    setFeedback(null);

    try {
      const res = await fetch(`/api/reminders/${id}/cancel`, {
        method: "POST",
        cache: "no-store",
      });
      const data: ApiCancelReminderResponse = await res.json();

      if (data.available === false) {
        setFeedback({
          type: "error",
          text: `Backend unavailable: ${data.error || "Could not reach Flask API"}`,
        });
      } else if (data.success === false) {
        const errorMsg =
          data.error === "Pending reminder not found."
            ? "This reminder is no longer pending and cannot be cancelled."
            : data.error || "Failed to cancel reminder.";

        setFeedback({
          type: "error",
          text: errorMsg,
        });
        // Refresh to sync latest state
        await fetchReminders();
      } else {
        setFeedback({
          type: "success",
          text: `Reminder #${id} was successfully cancelled.`,
        });
        // Refresh to update reminder list with cancelled state
        await fetchReminders();
      }
    } catch (err: unknown) {
      setFeedback({
        type: "error",
        text: err instanceof Error ? err.message : "Cancellation request failed",
      });
    } finally {
      setCancellingId(null);
    }
  };

  const isAvailable = response?.available === true;

  // Check if reminder_time is in the past
  const isPastTime = (timeStr?: string): boolean => {
    if (!timeStr) return false;
    try {
      const parsed = new Date(timeStr.replace(" ", "T"));
      return !isNaN(parsed.getTime()) && parsed < new Date();
    } catch {
      return false;
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reminders"
        description="Automated temporal reminders managed by the EchoMind Reminder Manager."
        badge={
          loading
            ? "Loading..."
            : isAvailable
            ? `${allReminders.length} Total Reminder${allReminders.length === 1 ? "" : "s"}`
            : "Backend Offline"
        }
        actions={
          <button
            type="button"
            onClick={fetchReminders}
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

      {/* Backend Unavailable Alert */}
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
                  The Next.js API proxy cannot connect to the EchoMind Flask API to load reminders.
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

      {/* Operation Feedback Banner (Cancellation Success or Error) */}
      {feedback && (
        <div
          className={`flex items-start justify-between gap-3 rounded-xl border p-4 text-xs shadow-xs ${
            feedback.type === "success"
              ? "border-emerald-200 bg-emerald-50 text-emerald-900"
              : "border-amber-200 bg-amber-50 text-amber-900"
          }`}
        >
          <div className="flex items-center gap-2">
            {feedback.type === "success" ? (
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
            ) : (
              <AlertCircle className="h-4 w-4 shrink-0 text-amber-600" />
            )}
            <span className="font-medium">{feedback.text}</span>
          </div>
          <button
            type="button"
            onClick={() => setFeedback(null)}
            className="text-slate-400 hover:text-slate-600 cursor-pointer"
            aria-label="Dismiss message"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Status Filter Pills */}
      {isAvailable && (
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 pb-4">
          <span className="text-xs font-medium text-slate-500 mr-1 flex items-center gap-1">
            <Tag className="h-3.5 w-3.5" /> Status:
          </span>
          {STATUS_FILTERS.map((st) => {
            const count = statusCounts[st] ?? 0;
            const isSelected = selectedStatus === st;
            return (
              <button
                key={st}
                type="button"
                onClick={() => setSelectedStatus(st)}
                className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all cursor-pointer ${
                  isSelected
                    ? "bg-indigo-600 text-white shadow-xs"
                    : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50 hover:text-slate-900"
                }`}
              >
                <span>{st}</span>
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
          {[1, 2].map((i) => (
            <div
              key={i}
              className="animate-pulse rounded-xl border border-slate-200 bg-white p-5 shadow-xs space-y-3"
            >
              <div className="flex items-center justify-between">
                <div className="h-5 bg-slate-200 rounded w-1/3"></div>
                <div className="h-5 bg-slate-200 rounded w-20"></div>
              </div>
              <div className="h-4 bg-slate-200 rounded w-full"></div>
              <div className="pt-2 border-t border-slate-100 flex gap-4">
                <div className="h-3 bg-slate-200 rounded w-32"></div>
                <div className="h-3 bg-slate-200 rounded w-24"></div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Reminders List Content */}
      {!loading && isAvailable && (
        <>
          {allReminders.length === 0 ? (
            /* Total Empty Store */
            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center shadow-xs">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-indigo-50 text-indigo-600">
                <Bell className="h-6 w-6" />
              </div>
              <h3 className="mt-3 text-base font-semibold text-slate-900">
                No Reminders Found
              </h3>
              <p className="mt-1 text-xs text-slate-500 max-w-md mx-auto">
                No reminders are currently registered in the database. When ambient speech or memory events produce commitments, they will be scheduled here.
              </p>
            </div>
          ) : filteredAndSortedReminders.length === 0 ? (
            /* Selected Filter Empty State */
            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center shadow-xs">
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-slate-500">
                <FileQuestion className="h-5 w-5" />
              </div>
              <h3 className="mt-2 text-sm font-semibold text-slate-900">
                No &ldquo;{selectedStatus}&rdquo; Reminders
              </h3>
              <p className="mt-1 text-xs text-slate-500">
                There are no reminders with status &ldquo;{selectedStatus}&rdquo;.
              </p>
              <button
                type="button"
                onClick={() => setSelectedStatus("All")}
                className="mt-3 inline-flex items-center gap-1 rounded-lg bg-indigo-50 px-3 py-1.5 text-xs font-semibold text-indigo-700 hover:bg-indigo-100 transition-colors cursor-pointer"
              >
                View all reminders ({allReminders.length})
              </button>
            </div>
          ) : (
            /* List of Reminders */
            <div className="space-y-4">
              {filteredAndSortedReminders.map((reminder) => {
                const normStatus = reminder.status.trim().toLowerCase();
                const isPending = normStatus === "pending";
                const isTriggered = normStatus === "triggered";
                const isCancelled = normStatus === "cancelled";
                const isOverdue = isPending && isPastTime(reminder.reminder_time);
                const isCancelling = cancellingId === reminder.id;
                const isConfirming = confirmCancelId === reminder.id;

                return (
                  <div
                    key={reminder.id}
                    className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs transition-all hover:border-indigo-200 hover:shadow-sm"
                  >
                    {/* Header: Title & Status Badge */}
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <h2 className="text-base font-semibold text-slate-900">
                            {reminder.title}
                          </h2>
                          <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-mono text-slate-600 border border-slate-200">
                            Memory #{reminder.memory_id}
                          </span>
                        </div>
                      </div>

                      {/* Distinct Visual Status Badges */}
                      <div className="flex items-center gap-2">
                        {isPending && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-[11px] font-bold tracking-wide text-amber-800 ring-1 ring-inset ring-amber-600/20">
                            <span className="h-1.5 w-1.5 rounded-full bg-amber-500"></span>
                            PENDING
                          </span>
                        )}

                        {isTriggered && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] font-bold tracking-wide text-emerald-800 ring-1 ring-inset ring-emerald-600/20">
                            <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                            TRIGGERED
                          </span>
                        )}

                        {isCancelled && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-bold tracking-wide text-slate-700 ring-1 ring-inset ring-slate-300">
                            <XCircle className="h-3 w-3 text-slate-500" />
                            CANCELLED
                          </span>
                        )}

                        {isOverdue && (
                          <span className="rounded-full bg-rose-50 px-2 py-0.5 text-[10px] font-semibold text-rose-700 ring-1 ring-inset ring-rose-600/20">
                            Overdue
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Content */}
                    <p className="mt-3 text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {reminder.content}
                    </p>

                    {/* Metadata Footer */}
                    <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-3 text-xs text-slate-500">
                      <div className="flex flex-wrap items-center gap-4">
                        <div className="flex items-center gap-1.5">
                          <Clock className="h-3.5 w-3.5 text-slate-400" />
                          <span>
                            Reminder Time:{" "}
                            <strong className="text-slate-700 font-medium">
                              {reminder.reminder_time || "Not scheduled"}
                            </strong>
                          </span>
                        </div>

                        {reminder.triggered_at && (
                          <div className="flex items-center gap-1.5 text-emerald-700">
                            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                            <span>Triggered: {reminder.triggered_at}</span>
                          </div>
                        )}

                        {reminder.created_at && (
                          <div className="flex items-center gap-1 text-slate-400">
                            <Calendar className="h-3 w-3" />
                            <span>Created: {reminder.created_at}</span>
                          </div>
                        )}
                      </div>

                      {/* Cancellation Actions (Shown ONLY for Pending Reminders) */}
                      {isPending && (
                        <div>
                          {isConfirming ? (
                            /* Inline Confirmation */
                            <div className="flex items-center gap-2 rounded-lg bg-rose-50 border border-rose-200 p-1.5">
                              <span className="text-[11px] font-semibold text-rose-900">
                                Confirm cancel?
                              </span>
                              <button
                                type="button"
                                onClick={() => handleConfirmCancel(reminder.id)}
                                disabled={isCancelling}
                                className="inline-flex items-center gap-1 rounded bg-rose-600 px-2 py-1 text-[11px] font-semibold text-white hover:bg-rose-700 transition-colors cursor-pointer"
                              >
                                {isCancelling ? (
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                ) : (
                                  <Check className="h-3 w-3" />
                                )}
                                <span>Yes, Cancel</span>
                              </button>
                              <button
                                type="button"
                                onClick={() => setConfirmCancelId(null)}
                                disabled={isCancelling}
                                className="inline-flex items-center rounded border border-slate-300 bg-white px-2 py-1 text-[11px] font-semibold text-slate-600 hover:bg-slate-50 transition-colors cursor-pointer"
                              >
                                Keep
                              </button>
                            </div>
                          ) : (
                            /* Cancel Button */
                            <button
                              type="button"
                              onClick={() => setConfirmCancelId(reminder.id)}
                              disabled={isCancelling}
                              className="inline-flex items-center gap-1.5 rounded-lg border border-rose-200 bg-rose-50/60 px-3 py-1.5 text-xs font-semibold text-rose-700 hover:bg-rose-100 hover:text-rose-800 transition-colors cursor-pointer disabled:opacity-50"
                            >
                              {isCancelling ? (
                                <>
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                  <span>Cancelling...</span>
                                </>
                              ) : (
                                <>
                                  <XCircle className="h-3.5 w-3.5 text-rose-600" />
                                  <span>Cancel Reminder</span>
                                </>
                              )}
                            </button>
                          )}
                        </div>
                      )}
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
