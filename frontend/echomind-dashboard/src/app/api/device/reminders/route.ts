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

function getRequiredEnvironmentVariable(name: string): string {
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

  const receivedBuffer = Buffer.from(receivedToken);
  const expectedBuffer = Buffer.from(expectedToken);

  if (receivedBuffer.length !== expectedBuffer.length) {
    return false;
  }

  return timingSafeEqual(
    receivedBuffer,
    expectedBuffer
  );
}

function isValidDateTime(value: string): boolean {
  return !Number.isNaN(
    Date.parse(value)
  );
}

function validatePayload(
  payload: unknown
): payload is ReminderSyncPayload {
  if (
    typeof payload !== "object" ||
    payload === null
  ) {
    return false;
  }

  const data = payload as Partial<ReminderSyncPayload>;

  if (
    typeof data.deviceId !== "string" ||
    !data.deviceId.trim()
  ) {
    return false;
  }

  if (
    typeof data.localReminderId !== "number" ||
    !Number.isInteger(data.localReminderId) ||
    data.localReminderId < 1
  ) {
    return false;
  }

  if (
    data.localMemoryId !== undefined &&
    data.localMemoryId !== null &&
    (
      typeof data.localMemoryId !== "number" ||
      !Number.isInteger(data.localMemoryId) ||
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
    !isValidDateTime(data.reminderTime)
  ) {
    return false;
  }

  if (
    data.eventTime !== undefined &&
    data.eventTime !== null &&
    (
      typeof data.eventTime !== "string" ||
      !isValidDateTime(data.eventTime)
    )
  ) {
    return false;
  }

  return true;
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

    const expectedDeviceToken =
      getRequiredEnvironmentVariable(
        "ECHOMIND_DEVICE_SYNC_TOKEN"
      );

    const receivedDeviceToken =
      request.headers.get(
        "x-echomind-device-token"
      );

    if (
      !secureTokenMatches(
        receivedDeviceToken,
        expectedDeviceToken
      )
    ) {
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

    let payload: unknown;

    try {
      payload = await request.json();
    } catch {
      return NextResponse.json(
        {
          ok: false,
          error: "Request body must be valid JSON.",
        },
        {
          status: 400,
        }
      );
    }

    if (!validatePayload(payload)) {
      return NextResponse.json(
        {
          ok: false,
          error: "Invalid reminder payload.",
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
      `${supabaseUrl}/rest/v1/cloud_reminders` +
      "?on_conflict=source_device_id,source_reminder_id";

    const response = await fetch(
      endpoint,
      {
        method: "POST",
        headers: {
          apikey: supabaseSecretKey,
          "Content-Type": "application/json",

          Prefer:
            "resolution=merge-duplicates,return=representation",
        },
        body: JSON.stringify(
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
        JSON.parse(responseText);
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
        error: "Server configuration error.",
      },
      {
        status: 500,
      }
    );
  }
}