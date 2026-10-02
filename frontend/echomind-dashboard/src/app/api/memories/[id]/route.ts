import {
  NextRequest,
  NextResponse,
} from "next/server";

import {
  deleteBackendMemory,
  updateBackendMemory,
} from "@/lib/api/backend-client";

import {
  ApiMemoryMutationResponse,
  MemoryUpdatePayload,
} from "@/types/api";

export const dynamic =
  "force-dynamic";


function parseMemoryId(
  id: string,
): number | null {
  const parsed = Number.parseInt(
    id,
    10,
  );

  if (
    Number.isNaN(parsed) ||
    parsed < 1
  ) {
    return null;
  }

  return parsed;
}


export async function PUT(
  request: NextRequest,
  segmentData: {
    params: Promise<{
      id: string;
    }>;
  },
): Promise<
  NextResponse<ApiMemoryMutationResponse>
> {
  const {
    id,
  } = await segmentData.params;

  const memoryId =
    parseMemoryId(id);

  if (memoryId === null) {
    return NextResponse.json(
      {
        available: true,
        success: false,
        error:
          "Invalid memory ID.",
      },
      {
        status: 400,
      },
    );
  }

  let body: unknown;

  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      {
        available: true,
        success: false,
        error:
          "Valid JSON body required.",
      },
      {
        status: 400,
      },
    );
  }

  if (
    typeof body !== "object" ||
    body === null
  ) {
    return NextResponse.json(
      {
        available: true,
        success: false,
        error:
          "Memory data is required.",
      },
      {
        status: 400,
      },
    );
  }

  const data =
    body as Partial<MemoryUpdatePayload>;

  if (
    typeof data.category !==
      "string" ||
    !data.category.trim() ||
    typeof data.title !==
      "string" ||
    !data.title.trim() ||
    typeof data.content !==
      "string" ||
    !data.content.trim() ||
    typeof data.date !==
      "string" ||
    typeof data.time !==
      "string" ||
    typeof data.notification !==
      "boolean"
  ) {
    return NextResponse.json(
      {
        available: true,
        success: false,
        error:
          "Invalid memory data.",
      },
      {
        status: 400,
      },
    );
  }

  const payload:
    MemoryUpdatePayload = {
      category:
        data.category.trim(),

      title:
        data.title.trim(),

      content:
        data.content.trim(),

      date:
        data.date,

      time:
        data.time,

      notification:
        data.notification,
    };

  const result =
    await updateBackendMemory(
      memoryId,
      payload,
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


export async function DELETE(
  _request: NextRequest,
  segmentData: {
    params: Promise<{
      id: string;
    }>;
  },
): Promise<
  NextResponse<ApiMemoryMutationResponse>
> {
  const {
    id,
  } = await segmentData.params;

  const memoryId =
    parseMemoryId(id);

  if (memoryId === null) {
    return NextResponse.json(
      {
        available: true,
        success: false,
        error:
          "Invalid memory ID.",
      },
      {
        status: 400,
      },
    );
  }

  const result =
    await deleteBackendMemory(
      memoryId,
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