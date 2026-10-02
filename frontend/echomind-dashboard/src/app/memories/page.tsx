"use client";

import React, {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import { PageHeader } from "@/components/common/PageHeader";

import {
  formatDate,
  formatTime,
} from "@/lib/formatters";

import {
  ApiMemoriesResponse,
  ApiMemoryMutationResponse,
  Memory,
  MemoryCategory,
  MemoryUpdatePayload,
} from "@/types/api";

import {
  AlertTriangle,
  Bell,
  BellOff,
  Brain,
  Calendar,
  Check,
  CheckCircle2,
  Clock,
  FileQuestion,
  Loader2,
  Pencil,
  RefreshCw,
  Repeat,
  Tag,
  Trash2,
  X,
} from "lucide-react";

const CATEGORIES: MemoryCategory[] = [
  "All",
  "Reminder",
  "Task",
  "Shopping",
  "Note",
  "Preference",
  "Event",
];

const EDITABLE_CATEGORIES = [
  "Reminder",
  "Task",
  "Shopping",
  "Note",
  "Preference",
  "Event",
];

export default function MemoriesPage() {
  const [response, setResponse] =
    useState<ApiMemoriesResponse | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [
    selectedCategory,
    setSelectedCategory,
  ] =
    useState<MemoryCategory>("All");

  const [
    editingMemory,
    setEditingMemory,
  ] =
    useState<Memory | null>(null);

  const [
    editForm,
    setEditForm,
  ] =
    useState<MemoryUpdatePayload | null>(null);

  const [saving, setSaving] =
    useState(false);

  const [
    deleteConfirmId,
    setDeleteConfirmId,
  ] =
    useState<number | null>(null);

  const [
    deletingId,
    setDeletingId,
  ] =
    useState<number | null>(null);

  const [
    clearConfirmOpen,
    setClearConfirmOpen,
  ] =
    useState(false);

  const [clearing, setClearing] =
    useState(false);

  const [feedback, setFeedback] =
    useState<{
      type: "success" | "error";
      text: string;
    } | null>(null);

  const fetchMemories =
    useCallback(async () => {
      setLoading(true);

      try {
        const result =
          await fetch(
            "/api/memories",
            {
              cache: "no-store",
            },
          );

        const data =
          (await result.json()) as ApiMemoriesResponse;

        setResponse(data);
      } catch (error: unknown) {
        setResponse({
          available: false,

          error:
            error instanceof Error
              ? error.message
              : "Failed to load memories.",
        });
      } finally {
        setLoading(false);
      }
    }, []);

  useEffect(() => {
    fetchMemories();
  }, [fetchMemories]);

  const allMemories =
    useMemo(() => {
      if (
        response?.available &&
        response.memories
      ) {
        return response.memories;
      }

      return [];
    }, [response]);

  const filteredMemories =
    useMemo(() => {
      if (
        selectedCategory ===
        "All"
      ) {
        return allMemories;
      }

      return allMemories.filter(
        (memory) =>
          memory.category
            .trim()
            .toLowerCase() ===
          selectedCategory
            .toLowerCase(),
      );
    }, [
      allMemories,
      selectedCategory,
    ]);

  const categoryCounts =
    useMemo(() => {
      const counts:
        Record<string, number> = {
          All: allMemories.length,
        };

      for (
        const category
        of CATEGORIES
      ) {
        if (
          category ===
          "All"
        ) {
          continue;
        }

        counts[category] =
          allMemories.filter(
            (memory) =>
              memory.category
                .trim()
                .toLowerCase() ===
              category
                .toLowerCase(),
          ).length;
      }

      return counts;
    }, [allMemories]);

  const isAvailable =
    response?.available === true;

  const startEditing =
    (memory: Memory) => {
      setFeedback(null);

      setEditingMemory(memory);

      setEditForm({
        category:
          memory.category,

        title:
          memory.title,

        content:
          memory.content,

        date:
          memory.date || "",

        time:
          memory.time || "",

        notification:
          memory.notification,
      });
    };

  const cancelEditing =
    () => {
      setEditingMemory(null);
      setEditForm(null);
    };

  const updateEditField =
    <
      K extends keyof MemoryUpdatePayload,
    >(
      field: K,
      value: MemoryUpdatePayload[K],
    ) => {
      setEditForm(
        (current) => {
          if (!current) {
            return current;
          }

          return {
            ...current,
            [field]: value,
          };
        },
      );
    };

  const saveMemory =
    async () => {
      if (
        !editingMemory ||
        !editForm
      ) {
        return;
      }

      if (
        !editForm.title.trim() ||
        !editForm.content.trim() ||
        !editForm.category.trim()
      ) {
        setFeedback({
          type: "error",
          text:
            "Title, content and category are required.",
        });

        return;
      }

      setSaving(true);
      setFeedback(null);

      try {
        const result =
          await fetch(
            `/api/memories/${editingMemory.id}`,
            {
              method: "PUT",

              headers: {
                "Content-Type":
                  "application/json",
              },

              body:
                JSON.stringify({
                  ...editForm,

                  title:
                    editForm.title.trim(),

                  content:
                    editForm.content.trim(),

                  category:
                    editForm.category.trim(),
                }),

              cache: "no-store",
            },
          );

        const data =
          (await result.json()) as ApiMemoryMutationResponse;

        if (
          !result.ok ||
          data.available === false ||
          data.success !== true
        ) {
          throw new Error(
            data.error ||
              "Unable to update memory.",
          );
        }

        setFeedback({
          type: "success",
          text:
            "Memory updated successfully.",
        });

        cancelEditing();

        await fetchMemories();
      } catch (error: unknown) {
        setFeedback({
          type: "error",

          text:
            error instanceof Error
              ? error.message
              : "Unable to update memory.",
        });
      } finally {
        setSaving(false);
      }
    };

  const deleteMemory =
    async (
      memoryId: number,
    ) => {
      setDeletingId(memoryId);
      setFeedback(null);

      try {
        const result =
          await fetch(
            `/api/memories/${memoryId}`,
            {
              method: "DELETE",
              cache: "no-store",
            },
          );

        const data =
          (await result.json()) as ApiMemoryMutationResponse;

        if (
          !result.ok ||
          data.available === false ||
          data.success !== true
        ) {
          throw new Error(
            data.error ||
              "Unable to delete memory.",
          );
        }

        setFeedback({
          type: "success",
          text:
            "Memory deleted successfully.",
        });

        setDeleteConfirmId(null);

        await fetchMemories();
      } catch (error: unknown) {
        setFeedback({
          type: "error",

          text:
            error instanceof Error
              ? error.message
              : "Unable to delete memory.",
        });
      } finally {
        setDeletingId(null);
      }
    };

  const clearAllMemories =
    async () => {
      setClearing(true);
      setFeedback(null);

      try {
        const result =
          await fetch(
            "/api/memories",
            {
              method: "DELETE",
              cache: "no-store",
            },
          );

        const data =
          (await result.json()) as ApiMemoryMutationResponse;

        if (
          !result.ok ||
          data.available === false ||
          data.success !== true
        ) {
          throw new Error(
            data.error ||
              "Unable to clear memories.",
          );
        }

        setFeedback({
          type: "success",

          text:
            "All memories and associated pending reminders were cleared.",
        });

        setClearConfirmOpen(false);

        await fetchMemories();
      } catch (error: unknown) {
        setFeedback({
          type: "error",

          text:
            error instanceof Error
              ? error.message
              : "Unable to clear memories.",
        });
      } finally {
        setClearing(false);
      }
    };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Memories"
        description="Review, update and manage important information remembered by EchoMind."
        badge={
          loading
            ? "Loading..."
            : isAvailable
              ? `${allMemories.length} Saved`
              : undefined
        }
        actions={
          <div className="flex flex-wrap items-center gap-2">
            {isAvailable &&
              allMemories.length >
                0 && (
                <button
                  type="button"
                  onClick={() =>
                    setClearConfirmOpen(
                      true,
                    )
                  }
                  disabled={clearing}
                  className="inline-flex items-center gap-2 rounded-xl border border-rose-200 bg-white px-3.5 py-2 text-xs font-semibold text-rose-700 shadow-sm transition hover:bg-rose-50 disabled:opacity-50"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Clear All
                </button>
              )}

            <button
              type="button"
              onClick={fetchMemories}
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
          </div>
        }
      />

      {feedback && (
        <div
          className={`flex items-start justify-between gap-3 rounded-2xl border px-4 py-3 text-xs shadow-sm ${
            feedback.type ===
            "success"
              ? "border-emerald-200 bg-emerald-50 text-emerald-900"
              : "border-rose-200 bg-rose-50 text-rose-900"
          }`}
        >
          <div className="flex items-center gap-2">
            {feedback.type ===
            "success" ? (
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
            ) : (
              <AlertTriangle className="h-4 w-4 shrink-0 text-rose-600" />
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
            aria-label="Dismiss"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {clearConfirmOpen && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-5 shadow-sm">
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-rose-100 text-rose-700">
                <AlertTriangle className="h-5 w-5" />
              </div>

              <div>
                <h3 className="text-sm font-bold text-rose-950">
                  Clear all EchoMind memories?
                </h3>

                <p className="mt-1 max-w-xl text-xs leading-relaxed text-rose-800">
                  This permanently removes all saved memories and cancels pending reminders associated with them.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() =>
                  setClearConfirmOpen(
                    false,
                  )
                }
                disabled={clearing}
                className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
              >
                Keep Memories
              </button>

              <button
                type="button"
                onClick={
                  clearAllMemories
                }
                disabled={clearing}
                className="inline-flex items-center gap-2 rounded-xl bg-rose-600 px-3 py-2 text-xs font-bold text-white transition hover:bg-rose-700 disabled:opacity-50"
              >
                {clearing ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Trash2 className="h-3.5 w-3.5" />
                )}

                {clearing
                  ? "Clearing..."
                  : "Clear Everything"}
              </button>
            </div>
          </div>
        </div>
      )}

      {!loading &&
        !isAvailable && (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 shadow-sm">
            <div className="flex items-start gap-3">
              <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />

              <div>
                <h3 className="text-sm font-bold text-amber-950">
                  EchoMind is unavailable
                </h3>

                <p className="mt-1 text-xs text-amber-800">
                  Start the Python EchoMind backend and refresh this page.
                </p>
              </div>
            </div>
          </div>
        )}

      {isAvailable && (
        <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-slate-200/80 bg-white/80 p-3 shadow-sm">
          <span className="mr-1 flex items-center gap-1.5 text-xs font-semibold text-slate-500">
            <Tag className="h-3.5 w-3.5" />
            Filter
          </span>

          {CATEGORIES.map(
            (
              category,
            ) => {
              const selected =
                selectedCategory ===
                category;

              return (
                <button
                  key={category}
                  type="button"
                  onClick={() =>
                    setSelectedCategory(
                      category,
                    )
                  }
                  className={`inline-flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs font-semibold transition ${
                    selected
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "border border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  {category}

                  <span
                    className={`rounded-full px-1.5 py-0.5 text-[9px] font-bold ${
                      selected
                        ? "bg-white/15 text-white"
                        : "bg-slate-100 text-slate-500"
                    }`}
                  >
                    {categoryCounts[
                      category
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
          {[1, 2, 3].map(
            (
              value,
            ) => (
              <div
                key={value}
                className="animate-pulse rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
              >
                <div className="h-5 w-1/3 rounded bg-slate-200" />

                <div className="mt-4 h-4 w-full rounded bg-slate-200" />

                <div className="mt-2 h-4 w-2/3 rounded bg-slate-200" />
              </div>
            ),
          )}
        </div>
      )}

      {!loading &&
        isAvailable &&
        allMemories.length ===
          0 && (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white/80 p-12 text-center shadow-sm">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
              <Brain className="h-6 w-6" />
            </div>

            <h3 className="mt-4 text-base font-bold text-slate-950">
              No memories saved yet
            </h3>

            <p className="mx-auto mt-1 max-w-md text-xs leading-relaxed text-slate-500">
              Important information detected from conversations will appear here.
            </p>
          </div>
        )}

      {!loading &&
        isAvailable &&
        allMemories.length >
          0 &&
        filteredMemories.length ===
          0 && (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
            <FileQuestion className="mx-auto h-7 w-7 text-slate-400" />

            <h3 className="mt-3 text-sm font-bold text-slate-900">
              No {selectedCategory} memories
            </h3>

            <button
              type="button"
              onClick={() =>
                setSelectedCategory(
                  "All",
                )
              }
              className="mt-3 text-xs font-bold text-indigo-600"
            >
              View all memories
            </button>
          </div>
        )}

      {!loading &&
        isAvailable &&
        filteredMemories.length >
          0 && (
          <div className="space-y-4">
            {filteredMemories.map(
              (
                memory,
              ) => {
                const hasSupersedes =
                  memory.supersedes_id !==
                    null &&
                  memory.supersedes_id !==
                    undefined;

                const duplicate =
                  memory.seen_count >
                  1;

                const missingDate =
                  !memory.date ||
                  !memory.date.trim();

                const missingTime =
                  !memory.time ||
                  !memory.time.trim();

                const waitingForTime =
                  memory.notification &&
                  (
                    missingDate ||
                    missingTime
                  );

                const isEditing =
                  editingMemory?.id ===
                  memory.id;

                const confirmingDelete =
                  deleteConfirmId ===
                  memory.id;

                const deleting =
                  deletingId ===
                  memory.id;

                return (
                  <div
                    key={memory.id}
                    className="rounded-2xl border border-slate-200/80 bg-white/90 p-5 shadow-[0_8px_30px_rgba(15,23,42,0.04)] transition hover:border-indigo-200 hover:shadow-md sm:p-6"
                  >
                    {isEditing &&
                    editForm ? (
                      <div className="space-y-5">
                        <div className="flex items-center justify-between">
                          <div>
                            <h2 className="text-base font-bold text-slate-950">
                              Edit Memory
                            </h2>

                            <p className="mt-1 text-xs text-slate-500">
                              Update the saved information below.
                            </p>
                          </div>

                          <button
                            type="button"
                            onClick={
                              cancelEditing
                            }
                            disabled={saving}
                            className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 text-slate-500 hover:bg-slate-50"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </div>

                        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                          <label className="space-y-1.5 text-xs font-semibold text-slate-600">
                            Category

                            <select
                              value={
                                editForm.category
                              }
                              onChange={(
                                event,
                              ) =>
                                updateEditField(
                                  "category",
                                  event.target.value,
                                )
                              }
                              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-normal text-slate-900"
                            >
                              {EDITABLE_CATEGORIES.map(
                                (
                                  category,
                                ) => (
                                  <option
                                    key={
                                      category
                                    }
                                    value={
                                      category
                                    }
                                  >
                                    {category}
                                  </option>
                                ),
                              )}
                            </select>
                          </label>

                          <label className="space-y-1.5 text-xs font-semibold text-slate-600">
                            Title

                            <input
                              value={
                                editForm.title
                              }
                              onChange={(
                                event,
                              ) =>
                                updateEditField(
                                  "title",
                                  event.target.value,
                                )
                              }
                              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-normal text-slate-900"
                            />
                          </label>

                          <label className="space-y-1.5 text-xs font-semibold text-slate-600 md:col-span-2">
                            Content

                            <textarea
                              value={
                                editForm.content
                              }
                              onChange={(
                                event,
                              ) =>
                                updateEditField(
                                  "content",
                                  event.target.value,
                                )
                              }
                              rows={4}
                              className="w-full resize-none rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-normal text-slate-900"
                            />
                          </label>

                          <label className="space-y-1.5 text-xs font-semibold text-slate-600">
                            Date

                            <input
                              type="date"
                              value={
                                editForm.date
                              }
                              onChange={(
                                event,
                              ) =>
                                updateEditField(
                                  "date",
                                  event.target.value,
                                )
                              }
                              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-normal text-slate-900"
                            />
                          </label>

                          <label className="space-y-1.5 text-xs font-semibold text-slate-600">
                            Time

                            <input
                              type="time"
                              value={
                                editForm.time
                              }
                              onChange={(
                                event,
                              ) =>
                                updateEditField(
                                  "time",
                                  event.target.value,
                                )
                              }
                              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-normal text-slate-900"
                            />
                          </label>
                        </div>

                        <label className="flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                          <input
                            type="checkbox"
                            checked={
                              editForm.notification
                            }
                            onChange={(
                              event,
                            ) =>
                              updateEditField(
                                "notification",
                                event.target.checked,
                              )
                            }
                            className="h-4 w-4 accent-indigo-600"
                          />

                          <div>
                            <p className="text-xs font-bold text-slate-800">
                              Enable reminder
                            </p>

                            <p className="text-[10px] text-slate-500">
                              A reminder is only scheduled when both date and time are available.
                            </p>
                          </div>
                        </label>

                        <div className="flex justify-end gap-2 border-t border-slate-100 pt-4">
                          <button
                            type="button"
                            onClick={
                              cancelEditing
                            }
                            disabled={saving}
                            className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                          >
                            Cancel
                          </button>

                          <button
                            type="button"
                            onClick={
                              saveMemory
                            }
                            disabled={saving}
                            className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white transition hover:bg-indigo-700 disabled:opacity-50"
                          >
                            {saving ? (
                              <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            ) : (
                              <Check className="h-3.5 w-3.5" />
                            )}

                            {saving
                              ? "Saving..."
                              : "Save Changes"}
                          </button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
                          <div className="min-w-0">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-[10px] font-bold text-slate-600">
                                {memory.category ||
                                  "General"}
                              </span>

                              <h2 className="text-base font-bold text-slate-950">
                                {memory.title}
                              </h2>
                            </div>

                            <div className="mt-2 flex flex-wrap gap-1.5">
                              <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-[10px] font-bold text-emerald-700 ring-1 ring-emerald-600/15">
                                ACTIVE
                              </span>

                              {hasSupersedes && (
                                <span className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-[10px] font-bold text-indigo-700 ring-1 ring-indigo-600/15">
                                  UPDATED
                                </span>
                              )}

                              {duplicate && (
                                <span className="rounded-full bg-amber-50 px-2.5 py-0.5 text-[10px] font-bold text-amber-700 ring-1 ring-amber-600/15">
                                  Mentioned {memory.seen_count} times
                                </span>
                              )}
                            </div>
                          </div>

                          <div className="flex shrink-0 items-center gap-2">
                            <button
                              type="button"
                              onClick={() =>
                                startEditing(
                                  memory,
                                )
                              }
                              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700"
                            >
                              <Pencil className="h-3.5 w-3.5" />
                              Edit
                            </button>

                            {!confirmingDelete && (
                              <button
                                type="button"
                                onClick={() =>
                                  setDeleteConfirmId(
                                    memory.id,
                                  )
                                }
                                className="inline-flex items-center gap-1.5 rounded-xl border border-rose-200 bg-white px-3 py-1.5 text-xs font-semibold text-rose-700 transition hover:bg-rose-50"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                                Delete
                              </button>
                            )}
                          </div>
                        </div>

                        <p className="mt-4 whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
                          {memory.content}
                        </p>

                        {waitingForTime && (
                          <div className="mt-4 flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
                            <Clock className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />

                            <div>
                              <p className="text-xs font-bold text-amber-900">
                                Waiting for time information
                              </p>

                              <p className="mt-0.5 text-[10px] leading-relaxed text-amber-700">
                                EchoMind remembered this information, but a notification cannot be scheduled until a complete date and time are available.
                              </p>
                            </div>
                          </div>
                        )}

                        <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-slate-100 pt-4 text-xs text-slate-500">
                          <span className="inline-flex items-center gap-1.5">
                            <Calendar className="h-3.5 w-3.5 text-slate-400" />

                            {missingDate
                              ? "No date specified"
                              : formatDate(
                                  memory.date,
                                )}
                          </span>

                          <span className="inline-flex items-center gap-1.5">
                            <Clock className="h-3.5 w-3.5 text-slate-400" />

                            {missingTime
                              ? "No time specified"
                              : formatTime(
                                  memory.time,
                                )}
                          </span>

                          <span className="inline-flex items-center gap-1.5">
                            {memory.notification ? (
                              <Bell className="h-3.5 w-3.5 text-indigo-500" />
                            ) : (
                              <BellOff className="h-3.5 w-3.5 text-slate-400" />
                            )}

                            {memory.notification
                              ? waitingForTime
                                ? "Reminder requested — not scheduled"
                                : "Reminder enabled"
                              : "No reminder requested"}
                          </span>

                          {hasSupersedes && (
                            <span className="inline-flex items-center gap-1.5 text-indigo-600">
                              <Repeat className="h-3.5 w-3.5" />

                              Updated previous memory #{memory.supersedes_id}
                            </span>
                          )}
                        </div>

                        {confirmingDelete && (
                          <div className="mt-4 flex flex-col justify-between gap-3 rounded-xl border border-rose-200 bg-rose-50 p-3 sm:flex-row sm:items-center">
                            <div>
                              <p className="text-xs font-bold text-rose-900">
                                Delete this memory?
                              </p>

                              <p className="mt-0.5 text-[10px] text-rose-700">
                                Any pending reminder linked to this memory will also be cancelled.
                              </p>
                            </div>

                            <div className="flex gap-2">
                              <button
                                type="button"
                                onClick={() =>
                                  setDeleteConfirmId(
                                    null,
                                  )
                                }
                                disabled={deleting}
                                className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700"
                              >
                                Keep
                              </button>

                              <button
                                type="button"
                                onClick={() =>
                                  deleteMemory(
                                    memory.id,
                                  )
                                }
                                disabled={deleting}
                                className="inline-flex items-center gap-1.5 rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-rose-700 disabled:opacity-50"
                              >
                                {deleting ? (
                                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                ) : (
                                  <Trash2 className="h-3.5 w-3.5" />
                                )}

                                {deleting
                                  ? "Deleting..."
                                  : "Delete Memory"}
                              </button>
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                );
              },
            )}
          </div>
        )}
    </div>
  );
}