import {
  ApiCancelReminderResponse,
  ApiMemoriesResponse,
  ApiRemindersResponse,
  ApiSearchResponse,
  ApiStatusResponse,
  Memory,
  MemorySearchResult,
  Reminder,
  SystemStatus,
} from "@/types/api";

/**
 * EchoMind Flask Backend Server-Side Client.
 *
 * This client runs strictly on the server-side (Route Handlers / Server Components)
 * and proxies requests to the local Flask REST API.
 * Browser components NEVER call Flask directly and never expose ECHOMIND_API_URL.
 */
function getBackendUrl(): string {
  return process.env.ECHOMIND_API_URL || "http://127.0.0.1:5000";
}

/**
 * Fetch system status from Flask REST API GET /api/status.
 * Gracefully handles offline states, timeouts, and network errors.
 */
export async function fetchBackendStatus(): Promise<ApiStatusResponse> {
  const baseUrl = getBackendUrl();
  const endpoint = `${baseUrl}/api/status`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3500);

    const response = await fetch(endpoint, {
      method: "GET",
      signal: controller.signal,
      headers: {
        Accept: "application/json",
      },
      cache: "no-store",
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return {
        available: false,
        error: `Backend responded with HTTP ${response.status}: ${response.statusText}`,
      };
    }

    const data = (await response.json()) as SystemStatus;

    return {
      available: true,
      status: data,
    };
  } catch (err: unknown) {
    const errorMessage =
      err instanceof Error
        ? err.name === "AbortError"
          ? `Connection to Flask API timed out at ${baseUrl}`
          : err.message
        : "Failed to connect to Flask API";

    return {
      available: false,
      error: errorMessage,
    };
  }
}

/**
 * Fetch active memories from Flask REST API GET /api/memories.
 * Gracefully handles offline states, timeouts, and network errors.
 */
export async function fetchBackendMemories(): Promise<ApiMemoriesResponse> {
  const baseUrl = getBackendUrl();
  const endpoint = `${baseUrl}/api/memories`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3500);

    const response = await fetch(endpoint, {
      method: "GET",
      signal: controller.signal,
      headers: {
        Accept: "application/json",
      },
      cache: "no-store",
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return {
        available: false,
        error: `Backend responded with HTTP ${response.status}: ${response.statusText}`,
      };
    }

    const data = (await response.json()) as Memory[];

    return {
      available: true,
      memories: Array.isArray(data) ? data : [],
    };
  } catch (err: unknown) {
    const errorMessage =
      err instanceof Error
        ? err.name === "AbortError"
          ? `Connection to Flask API timed out at ${baseUrl}`
          : err.message
        : "Failed to connect to Flask API";

    return {
      available: false,
      error: errorMessage,
    };
  }
}

/**
 * Search active memories semantically using Flask REST API GET /api/memories/search?q=<query>.
 * If query is empty or whitespace only, returns empty list without calling Flask.
 */
export async function fetchBackendMemorySearch(
  query: string
): Promise<ApiSearchResponse> {
  const trimmed = query.trim();
  if (!trimmed) {
    return {
      available: true,
      results: [],
      query: "",
    };
  }

  const baseUrl = getBackendUrl();
  const endpoint = `${baseUrl}/api/memories/search?q=${encodeURIComponent(trimmed)}`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3500);

    const response = await fetch(endpoint, {
      method: "GET",
      signal: controller.signal,
      headers: {
        Accept: "application/json",
      },
      cache: "no-store",
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return {
        available: false,
        error: `Backend responded with HTTP ${response.status}: ${response.statusText}`,
        query: trimmed,
      };
    }

    const data = (await response.json()) as MemorySearchResult[];

    return {
      available: true,
      results: Array.isArray(data) ? data : [],
      query: trimmed,
    };
  } catch (err: unknown) {
    const errorMessage =
      err instanceof Error
        ? err.name === "AbortError"
          ? `Connection to Flask API timed out at ${baseUrl}`
          : err.message
        : "Failed to connect to Flask API";

    return {
      available: false,
      error: errorMessage,
      query: trimmed,
    };
  }
}

/**
 * Fetch all reminders from Flask REST API GET /api/reminders.
 * Gracefully handles offline states, timeouts, and network errors.
 */
export async function fetchBackendReminders(): Promise<ApiRemindersResponse> {
  const baseUrl = getBackendUrl();
  const endpoint = `${baseUrl}/api/reminders`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3500);

    const response = await fetch(endpoint, {
      method: "GET",
      signal: controller.signal,
      headers: {
        Accept: "application/json",
      },
      cache: "no-store",
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return {
        available: false,
        error: `Backend responded with HTTP ${response.status}: ${response.statusText}`,
      };
    }

    const data = (await response.json()) as Reminder[];

    return {
      available: true,
      reminders: Array.isArray(data) ? data : [],
    };
  } catch (err: unknown) {
    const errorMessage =
      err instanceof Error
        ? err.name === "AbortError"
          ? `Connection to Flask API timed out at ${baseUrl}`
          : err.message
        : "Failed to connect to Flask API";

    return {
      available: false,
      error: errorMessage,
    };
  }
}

/**
 * Cancel a pending reminder via Flask REST API POST /api/reminders/<id>/cancel.
 * Distinguishes backend availability from operation-level cancellation rejection (404).
 */
export async function cancelBackendReminder(
  id: number
): Promise<ApiCancelReminderResponse> {
  const baseUrl = getBackendUrl();
  const endpoint = `${baseUrl}/api/reminders/${id}/cancel`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3500);

    const response = await fetch(endpoint, {
      method: "POST",
      signal: controller.signal,
      headers: {
        Accept: "application/json",
      },
      cache: "no-store",
    });

    clearTimeout(timeoutId);

    // If 404, the Flask backend is available, but the reminder is not pending or not found
    if (response.status === 404) {
      const errorJson = (await response.json().catch(() => null)) as {
        error?: string;
      } | null;
      return {
        available: true,
        success: false,
        reminder_id: id,
        error: errorJson?.error || "Pending reminder not found.",
      };
    }

    if (!response.ok) {
      const errorJson = (await response.json().catch(() => null)) as {
        error?: string;
      } | null;
      return {
        available: true,
        success: false,
        reminder_id: id,
        error:
          errorJson?.error ||
          `Backend responded with HTTP ${response.status}: ${response.statusText}`,
      };
    }

    const data = (await response.json()) as {
      success: boolean;
      reminder_id: number;
    };

    return {
      available: true,
      success: data.success,
      reminder_id: data.reminder_id,
    };
  } catch (err: unknown) {
    const errorMessage =
      err instanceof Error
        ? err.name === "AbortError"
          ? `Connection to Flask API timed out at ${baseUrl}`
          : err.message
        : "Failed to connect to Flask API";

    return {
      available: false,
      success: false,
      error: errorMessage,
    };
  }
}
