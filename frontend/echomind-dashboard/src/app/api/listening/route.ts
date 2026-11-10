import {
  NextRequest,
  NextResponse,
} from "next/server";

import {
  updateBackendListening,
} from "@/lib/api/backend-client";

import {
  ApiListeningResponse,
} from "@/types/api";

export const dynamic =
  "force-dynamic";


export async function POST(
  request: NextRequest,
): Promise<
  NextResponse<ApiListeningResponse>
> {
  let body: unknown;

  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      {
        available: true,
        success: false,
        error: "Valid JSON body required.",
      },
      {
        status: 400,
      },
    );
  }

  if (
    typeof body !== "object" ||
    body === null ||
    !(
      "enabled" in body
    ) ||
    typeof (
      body as {
        enabled?: unknown;
      }
    ).enabled !== "boolean"
  ) {
    return NextResponse.json(
      {
        available: true,
        success: false,
        error:
          "enabled must be true or false.",
      },
      {
        status: 400,
      },
    );
  }

  const enabled = (
    body as {
      enabled: boolean;
    }
  ).enabled;

  const result =
    await updateBackendListening(
      enabled,
    );

  return NextResponse.json(
    result,
    {
      status: 200,

      headers: {
        "Cache-Control":
          "no-store, no-cache, must-revalidate",
      },
    },
  );
}