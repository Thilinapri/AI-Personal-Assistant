import {
  ApiMemoriesResponse,
  ApiSearchResponse,
  ApiStatusResponse,
  Memory,
  MemorySearchResult,
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
