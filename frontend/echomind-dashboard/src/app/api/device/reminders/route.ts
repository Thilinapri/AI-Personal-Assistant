import { timingSafeEqual } from "crypto";
import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

type ReminderSyncPayload = {
  deviceId: string;
  localReminderId: number;
  localMemoryId?: number | null;

  userId?: string | null;

  title: string;
  details?: string | null;

  eventTime?: string | null;
  reminderTime: string;

  reason?: string | null;

  notificationTitle?: string;
  notificationBody?: string;

  timezone?: string;
};

type ReminderCancelPayload = {
  deviceId: string;
  localReminderId: number;
};

function getRequiredEnvironmentVariable(
  name: string
): string {
  const value = process.env[name]?.trim();

  if (!value) {
    throw new Error(
      `Required environment variable ${name} is not configured.`
    );
  }

  return value;
}

function secureTokenMatches(
  receivedToken: string | null,
  expectedToken: string
): boolean {
  if (!receivedToken) {
    return false;
  }

  const receivedBuffer =
    Buffer.from(receivedToken);

  const expectedBuffer =
    Buffer.from(expectedToken);

  if (
    receivedBuffer.length !==
    expectedBuffer.length
  ) {
    return false;
  }

  return timingSafeEqual(
    receivedBuffer,
    expectedBuffer
  );
}

function isAuthorizedDevice(
  request: NextRequest
): boolean {
  const expectedToken =
    getRequiredEnvironmentVariable(
      "ECHOMIND_DEVICE_SYNC_TOKEN"
    );

  const receivedToken =
    request.headers.get(
      "x-echomind-device-token"
    );

  return secureTokenMatches(
    receivedToken,
    expectedToken
  );
}

function isValidDateTime(
  value: string
): boolean {
  return !Number.isNaN(
    Date.parse(value)
  );
}

function validateSyncPayload(
  payload: unknown
): payload is ReminderSyncPayload {
  if (
    typeof payload !== "object" ||
    payload === null
  ) {
    return false;
  }

  const data =
    payload as Partial<ReminderSyncPayload>;

  if (
    typeof data.deviceId !== "string" ||
    !data.deviceId.trim()
  ) {
    return false;
  }

  if (
    typeof data.localReminderId !== "number" ||
    !Number.isInteger(
      data.localReminderId
    ) ||
    data.localReminderId < 1
  ) {
    return false;
  }

  if (
    data.localMemoryId !== undefined &&
    data.localMemoryId !== null &&
    (
      typeof data.localMemoryId !== "number" ||
      !Number.isInteger(
        data.localMemoryId
      ) ||
      data.localMemoryId < 1
    )
  ) {
    return false;
  }

  if (
    typeof data.title !== "string" ||
    !data.title.trim()
  ) {
    return false;
  }

  if (
    typeof data.reminderTime !== "string" ||
    !isValidDateTime(
      data.reminderTime
    )
  ) {
    return false;
  }

  if (
    data.eventTime !== undefined &&
    data.eventTime !== null &&
    (
      typeof data.eventTime !== "string" ||
      !isValidDateTime(
        data.eventTime
      )
    )
  ) {
    return false;
  }

  return true;
}

function validateCancelPayload(
  payload: unknown
): payload is ReminderCancelPayload {
  if (
    typeof payload !== "object" ||
    payload === null
  ) {
    return false;
  }

  const data =
    payload as Partial<ReminderCancelPayload>;

  if (
    typeof data.deviceId !== "string" ||
    !data.deviceId.trim()
  ) {
    return false;
  }

  if (
    typeof data.localReminderId !== "number" ||
    !Number.isInteger(
      data.localReminderId
    ) ||
    data.localReminderId < 1
  ) {
    return false;
  }

  return true;
}

async function readJsonBody(
  request: NextRequest
): Promise<unknown | null> {
  try {
    return await request.json();
  } catch {
    return null;
  }
}

export async function POST(
  request: NextRequest
) {
  try {
    const supabaseUrl =
      getRequiredEnvironmentVariable(
        "SUPABASE_URL"
      );

    const supabaseSecretKey =
      getRequiredEnvironmentVariable(
        "SUPABASE_SECRET_KEY"
      );

    if (!isAuthorizedDevice(request)) {
      return NextResponse.json(
        {
          ok: false,
          error: "Unauthorized device.",
        },
        {
          status: 401,
        }
      );
    }

    const payload =
      await readJsonBody(request);

    if (payload === null) {
      return NextResponse.json(
        {
          ok: false,
          error:
            "Request body must be valid JSON.",
        },
        {
          status: 400,
        }
      );
    }

    if (
      !validateSyncPayload(
        payload
      )
    ) {
      return NextResponse.json(
        {
          ok: false,
          error:
            "Invalid reminder payload.",
        },
        {
          status: 400,
        }
      );
    }

    const cloudReminder = {
      source_device_id:
        payload.deviceId.trim(),

      source_reminder_id:
        payload.localReminderId,

      source_memory_id:
        payload.localMemoryId ?? null,

      user_id:
        payload.userId ?? null,

      title:
        payload.title.trim(),

      details:
        payload.details?.trim() || null,

      event_time:
        payload.eventTime ?? null,

      reminder_time:
        payload.reminderTime,

      reason:
        payload.reason?.trim() || null,

      notification_title:
        payload.notificationTitle?.trim() ||
        "EchoMind Reminder",

      notification_body:
        payload.notificationBody?.trim() ||
        "You have an upcoming reminder.",

      timezone:
        payload.timezone?.trim() ||
        "Asia/Colombo",

      status:
        "pending",

      updated_at:
        new Date().toISOString(),
    };

    const endpoint =
      `${supabaseUrl}` +
      "/rest/v1/cloud_reminders" +
      "?on_conflict=" +
      "source_device_id,source_reminder_id";

    const response =
      await fetch(
        endpoint,
        {
          method: "POST",

          headers: {
            apikey:
              supabaseSecretKey,

            "Content-Type":
              "application/json",

            Prefer:
              "resolution=merge-duplicates," +
              "return=representation",
          },

          body:
            JSON.stringify(
              cloudReminder
            ),

          cache: "no-store",
        }
      );

    const responseText =
      await response.text();

    if (!response.ok) {
      console.error(
        "Supabase reminder sync failed:",
        response.status,
        responseText
      );

      return NextResponse.json(
        {
          ok: false,
          error:
            "Cloud reminder synchronization failed.",
        },
        {
          status: 502,
        }
      );
    }

    let cloudData: unknown = null;

    if (responseText) {
      cloudData =
        JSON.parse(
          responseText
        );
    }

    return NextResponse.json(
      {
        ok: true,
        reminder: cloudData,
      },
      {
        status: 200,
      }
    );
  } catch (error: unknown) {
    const message =
      error instanceof Error
        ? error.message
        : "Unexpected server error.";

    console.error(
      "Cloud reminder API error:",
      message
    );

    return NextResponse.json(
      {
        ok: false,
        error:
          "Server configuration error.",
      },
      {
        status: 500,
      }
    );
  }
}

export async function PATCH(
  request: NextRequest
) {
  try {
    const supabaseUrl =
      getRequiredEnvironmentVariable(
        "SUPABASE_URL"
      );

    const supabaseSecretKey =
      getRequiredEnvironmentVariable(
        "SUPABASE_SECRET_KEY"
      );

    if (!isAuthorizedDevice(request)) {
      return NextResponse.json(
        {
          ok: false,
          error: "Unauthorized device.",
        },
        {
          status: 401,
        }
      );
    }

    const payload =
      await readJsonBody(request);

    if (payload === null) {
      return NextResponse.json(
        {
          ok: false,
          error:
            "Request body must be valid JSON.",
        },
        {
          status: 400,
        }
      );
    }

    if (
      !validateCancelPayload(
        payload
      )
    ) {
      return NextResponse.json(
        {
          ok: false,
          error:
            "Invalid reminder cancellation payload.",
        },
        {
          status: 400,
        }
      );
    }

    const query =
      new URLSearchParams({
        source_device_id:
          `eq.${payload.deviceId.trim()}`,

        source_reminder_id:
          `eq.${payload.localReminderId}`,

        status:
          "eq.pending",
      });

    const endpoint =
      `${supabaseUrl}` +
      "/rest/v1/cloud_reminders" +
      `?${query.toString()}`;

    const response =
      await fetch(
        endpoint,
        {
          method: "PATCH",

          headers: {
            apikey:
              supabaseSecretKey,

            "Content-Type":
              "application/json",

            Prefer:
              "return=representation",
          },

          body:
            JSON.stringify({
              status:
                "cancelled",

              updated_at:
                new Date().toISOString(),
            }),

          cache:
            "no-store",
        }
      );

    const responseText =
      await response.text();

    if (!response.ok) {
      console.error(
        "Supabase reminder cancellation failed:",
        response.status,
        responseText
      );

      return NextResponse.json(
        {
          ok: false,
          error:
            "Cloud reminder cancellation failed.",
        },
        {
          status: 502,
        }
      );
    }

    let updatedRows: unknown[] = [];

    if (responseText) {
      const parsed =
        JSON.parse(
          responseText
        );

      if (Array.isArray(parsed)) {
        updatedRows =
          parsed;
      }
    }

    return NextResponse.json(
      {
        ok: true,

        // false is still a successful/idempotent
        // cancellation request.
        updated:
          updatedRows.length > 0,

        reminder:
          updatedRows,
      },
      {
        status: 200,
      }
    );
  } catch (error: unknown) {
    const message =
      error instanceof Error
        ? error.message
        : "Unexpected server error.";

    console.error(
      "Cloud reminder cancellation error:",
      message
    );

    return NextResponse.json(
      {
        ok: false,
        error:
          "Server configuration error.",
      },
      {
        status: 500,
      }
    );
  }
}