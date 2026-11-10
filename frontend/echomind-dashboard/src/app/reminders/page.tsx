"use client";

import React, {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  formatDateTime,
} from "@/lib/formatters";

import {
  PageHeader,
} from "@/components/common/PageHeader";

import {
  ApiCancelReminderResponse,
  ApiRemindersResponse,
  ReminderStatusFilter,
} from "@/types/api";

import {
  AlertCircle,
  AlertTriangle,
  Bell,
  Check,
  CheckCircle2,
  Clock,
  FileQuestion,
  Loader2,
  RefreshCw,
  Tag,
  X,
  XCircle,
} from "lucide-react";

const STATUS_FILTERS: ReminderStatusFilter[] = [
  "All",
  "Pending",
  "Notified",
  "Cancelled",
];

export default function RemindersPage() {
  const [
    response,
    setResponse,
  ] = useState<ApiRemindersResponse | null>(null);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    selectedStatus,
    setSelectedStatus,
  ] = useState<ReminderStatusFilter>("All");

  const [
    cancellingId,
    setCancellingId,
  ] = useState<number | null>(null);

  const [
    confirmCancelId,
    setConfirmCancelId,
  ] = useState<number | null>(null);

  const [
    feedback,
    setFeedback,
  ] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const fetchReminders =
    useCallback(
      async (
        showLoading = true,
      ) => {
        if (showLoading) {
          setLoading(true);
        }

        try {
          const result =
            await fetch(
              "/api/reminders",
              {
                cache: "no-store",
              },
            );

          const data =
            (await result.json()) as ApiRemindersResponse;

          setResponse(data);
        } catch (
          error: unknown
        ) {
          setResponse({
            available: false,

            error:
              error instanceof Error
                ? error.message
                : "Failed to load reminders.",
          });
        } finally {
          if (showLoading) {
            setLoading(false);
          }
        }
      },
      [],
    );

  useEffect(() => {
    fetchReminders();

    const interval =
      window.setInterval(
        () => {
          fetchReminders(false);
        },
        5000,
      );

    return () => {
      window.clearInterval(
        interval,
      );
    };
  }, [fetchReminders]);

  const allReminders =
    useMemo(() => {
      if (
        response?.available &&
        response.reminders
      ) {
        return response.reminders;
      }

      return [];
    }, [response]);

  const statusCounts =
    useMemo(() => {
      const counts:
        Record<string, number> = {
          All: allReminders.length,
        };

      counts.Pending =
        allReminders.filter(
          (reminder) =>
            reminder.status
              .trim()
              .toLowerCase() ===
            "pending",
        ).length;

      counts.Notified =
        allReminders.filter(
          (reminder) => {
            const status =
              reminder.status
                .trim()
                .toLowerCase();

            return (
              status === "triggered" ||
              status === "notified"
            );
          },
        ).length;

      counts.Cancelled =
        allReminders.filter(
          (reminder) =>
            reminder.status
              .trim()
              .toLowerCase() ===
            "cancelled",
        ).length;

      return counts;
    }, [allReminders]);

  const filteredReminders =
    useMemo(() => {
      let reminders =
        [...allReminders];

      if (
        selectedStatus !== "All"
      ) {
        reminders =
          reminders.filter(
            (reminder) => {
              const status =
                reminder.status
                  .trim()
                  .toLowerCase();

              if (
                selectedStatus ===
                "Pending"
              ) {
                return (
                  status === "pending"
                );
              }

              if (
                selectedStatus ===
                "Notified"
              ) {
                return (
                  status === "triggered" ||
                  status === "notified"
                );
              }

              if (
                selectedStatus ===
                "Cancelled"
              ) {
                return (
                  status === "cancelled"
                );
              }

              return true;
            },
          );
      }

      reminders.sort(
        (
          first,
          second,
        ) => {
          const firstPending =
            first.status
              .trim()
              .toLowerCase() ===
            "pending";

          const secondPending =
            second.status
              .trim()
              .toLowerCase() ===
            "pending";

          if (
            firstPending &&
            secondPending
          ) {
            return (
              first.reminder_time ||
              ""
            ).localeCompare(
              second.reminder_time ||
              "",
            );
          }

          if (
            firstPending !==
            secondPending
          ) {
            return firstPending
              ? -1
              : 1;
          }

          return (
            second.reminder_time ||
            second.created_at ||
            ""
          ).localeCompare(
            first.reminder_time ||
            first.created_at ||
            "",
          );
        },
      );

      return reminders;
    }, [
      allReminders,
      selectedStatus,
    ]);

  const handleConfirmCancel =
    async (
      reminderId: number,
    ) => {
      setCancellingId(
        reminderId,
      );

      setConfirmCancelId(
        null,
      );

      setFeedback(null);

      try {
        const result =
          await fetch(
            `/api/reminders/${reminderId}/cancel`,
            {
              method: "POST",
              cache: "no-store",
            },
          );

        const data =
          (await result.json()) as ApiCancelReminderResponse;

        if (
          data.available === false
        ) {
          throw new Error(
            "EchoMind is currently unavailable.",
          );
        }

        if (
          data.success === false
        ) {
          throw new Error(
            data.error ||
              "Unable to cancel reminder.",
          );
        }

        setFeedback({
          type: "success",
          text:
            "Reminder cancelled successfully.",
        });

        await fetchReminders(
          false,
        );
      } catch (
        error: unknown
      ) {
        setFeedback({
          type: "error",

          text:
            error instanceof Error
              ? error.message
              : "Unable to cancel reminder.",
        });
      } finally {
        setCancellingId(
          null,
        );
      }
    };

  const isAvailable =
    response?.available === true;

  const isPastTime =
    (
      value?: string,
    ) => {
      if (!value) {
        return false;
      }

      const parsed =
        new Date(
          value.replace(
            " ",
            "T",
          ),
        );

      if (
        Number.isNaN(
          parsed.getTime(),
        )
      ) {
        return false;
      }

      return (
        parsed <
        new Date()
      );
    };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reminders"
        description="Upcoming, delivered and cancelled EchoMind reminders."
        badge={
          loading
            ? "Loading..."
            : isAvailable
              ? `${allReminders.length} Reminder${
                  allReminders.length === 1
                    ? ""
                    : "s"
                }`
              : undefined
        }
        actions={
          <button
            type="button"
            onClick={() =>
              fetchReminders()
            }
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm transition hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700 disabled:opacity-50"
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

      {feedback && (
        <div
          className={`flex items-start justify-between gap-3 rounded-2xl border p-4 text-xs shadow-sm ${
            feedback.type === "success"
              ? "border-emerald-200 bg-emerald-50 text-emerald-900"
              : "border-rose-200 bg-rose-50 text-rose-900"
          }`}
        >
          <div className="flex items-center gap-2">
            {feedback.type === "success" ? (
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
            ) : (
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
            )}

            <span className="font-medium">
              {feedback.text}
            </span>
          </div>

          <button
            type="button"
            onClick={() =>
              setFeedback(null)
            }
            className="text-slate-400 transition hover:text-slate-700"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {!loading &&
        !isAvailable && (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
            <div className="flex items-start gap-3">
              <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />

              <div>
                <h3 className="text-sm font-bold text-amber-950">
                  EchoMind is unavailable
                </h3>

                <p className="mt-1 text-xs text-amber-800">
                  Start the Python backend and refresh this page.
                </p>
              </div>
            </div>
          </div>
        )}

      {isAvailable && (
        <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-slate-200/80 bg-white/80 p-3 shadow-sm">
          <span className="mr-1 flex items-center gap-1.5 text-xs font-semibold text-slate-500">
            <Tag className="h-3.5 w-3.5" />
            Status
          </span>

          {STATUS_FILTERS.map(
            (
              status,
            ) => {
              const selected =
                selectedStatus ===
                status;

              return (
                <button
                  key={status}
                  type="button"
                  onClick={() =>
                    setSelectedStatus(
                      status,
                    )
                  }
                  className={`inline-flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs font-semibold transition ${
                    selected
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "border border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  {status}

                  <span
                    className={`rounded-full px-1.5 py-0.5 text-[9px] font-bold ${
                      selected
                        ? "bg-white/15 text-white"
                        : "bg-slate-100 text-slate-500"
                    }`}
                  >
                    {statusCounts[
                      status
                    ] ?? 0}
                  </span>
                </button>
              );
            },
          )}
        </div>
      )}

      {loading && (
        <div className="space-y-4">
          {[1, 2].map(
            (value) => (
              <div
                key={value}
                className="animate-pulse rounded-2xl border border-slate-200 bg-white p-5"
              >
                <div className="h-5 w-1/3 rounded bg-slate-200" />
                <div className="mt-4 h-4 w-full rounded bg-slate-200" />
              </div>
            ),
          )}
        </div>
      )}

      {!loading &&
        isAvailable &&
        allReminders.length === 0 && (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white/80 p-12 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-50 text-amber-600">
              <Bell className="h-6 w-6" />
            </div>

            <h3 className="mt-4 text-base font-bold text-slate-950">
              No reminders yet
            </h3>

            <p className="mx-auto mt-1 max-w-md text-xs leading-relaxed text-slate-500">
              EchoMind reminders will appear here when conversations contain scheduled information.
            </p>
          </div>
        )}

      {!loading &&
        isAvailable &&
        allReminders.length > 0 &&
        filteredReminders.length === 0 && (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
            <FileQuestion className="mx-auto h-7 w-7 text-slate-400" />

            <h3 className="mt-3 text-sm font-bold text-slate-900">
              No {selectedStatus} reminders
            </h3>

            <button
              type="button"
              onClick={() =>
                setSelectedStatus(
                  "All",
                )
              }
              className="mt-3 text-xs font-bold text-indigo-600"
            >
              View all reminders
            </button>
          </div>
        )}

      {!loading &&
        isAvailable &&
        filteredReminders.length > 0 && (
          <div className="space-y-4">
            {filteredReminders.map(
              (reminder) => {
                const status =
                  reminder.status
                    .trim()
                    .toLowerCase();

                const pending =
                  status === "pending";

                const notified =
                  status === "triggered" ||
                  status === "notified";

                const cancelled =
                  status === "cancelled";

                const overdue =
                  pending &&
                  isPastTime(
                    reminder.reminder_time,
                  );

                const cancelling =
                  cancellingId ===
                  reminder.id;

                const confirming =
                  confirmCancelId ===
                  reminder.id;

                return (
                  <div
                    key={reminder.id}
                    className="rounded-2xl border border-slate-200/80 bg-white/90 p-5 shadow-[0_8px_30px_rgba(15,23,42,0.04)] transition hover:border-indigo-200 hover:shadow-md sm:p-6"
                  >
                    <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
                      <div>
                        <h2 className="text-base font-bold text-slate-950">
                          {reminder.title}
                        </h2>

                        <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-slate-600">
                          {reminder.content}
                        </p>
                      </div>

                      <div className="flex flex-wrap items-center gap-2">
                        {pending && (
                          <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-2.5 py-1 text-[10px] font-bold text-amber-700 ring-1 ring-amber-600/15">
                            <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
                            PENDING
                          </span>
                        )}

                        {notified && (
                          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-[10px] font-bold text-emerald-700 ring-1 ring-emerald-600/15">
                            <CheckCircle2 className="h-3 w-3" />
                            NOTIFIED
                          </span>
                        )}

                        {cancelled && (
                          <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-bold text-slate-600 ring-1 ring-slate-300">
                            <XCircle className="h-3 w-3" />
                            CANCELLED
                          </span>
                        )}

                        {overdue && (
                          <span className="rounded-full bg-rose-50 px-2.5 py-1 text-[10px] font-bold text-rose-700 ring-1 ring-rose-600/15">
                            OVERDUE
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4">
                      <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500">
                        <span className="inline-flex items-center gap-1.5">
                          <Clock className="h-3.5 w-3.5 text-slate-400" />

                          <span>
                            {notified
                              ? "Scheduled:"
                              : "Remind at:"}{" "}

                            <strong className="font-semibold text-slate-700">
                              {formatDateTime(
                                reminder.reminder_time,
                              )}
                            </strong>
                          </span>
                        </span>

                        {reminder.triggered_at && (
                          <span className="inline-flex items-center gap-1.5 text-emerald-700">
                            <CheckCircle2 className="h-3.5 w-3.5" />

                            Notified{" "}
                            {formatDateTime(
                              reminder.triggered_at,
                            )}
                          </span>
                        )}
                      </div>

                      {pending && (
                        <div>
                          {confirming ? (
                            <div className="flex flex-wrap items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-2">
                              <span className="text-[10px] font-bold text-rose-900">
                                Cancel reminder?
                              </span>

                              <button
                                type="button"
                                onClick={() =>
                                  handleConfirmCancel(
                                    reminder.id,
                                  )
                                }
                                disabled={cancelling}
                                className="inline-flex items-center gap-1 rounded-lg bg-rose-600 px-2.5 py-1.5 text-[10px] font-bold text-white hover:bg-rose-700 disabled:opacity-50"
                              >
                                {cancelling ? (
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                ) : (
                                  <Check className="h-3 w-3" />
                                )}

                                Yes, Cancel
                              </button>

                              <button
                                type="button"
                                onClick={() =>
                                  setConfirmCancelId(
                                    null,
                                  )
                                }
                                disabled={cancelling}
                                className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-[10px] font-semibold text-slate-700"
                              >
                                Keep
                              </button>
                            </div>
                          ) : (
                            <button
                              type="button"
                              onClick={() =>
                                setConfirmCancelId(
                                  reminder.id,
                                )
                              }
                              className="inline-flex items-center gap-1.5 rounded-xl border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-700 transition hover:bg-rose-100"
                            >
                              <XCircle className="h-3.5 w-3.5" />

                              Cancel Reminder
                            </button>
                          )}
                        </div>
                      )}
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