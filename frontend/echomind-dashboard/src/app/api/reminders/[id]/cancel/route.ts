import { NextRequest, NextResponse } from "next/server";
import { cancelBackendReminder } from "@/lib/api/backend-client";
import { ApiCancelReminderResponse } from "@/types/api";

export const dynamic = "force-dynamic";

export async function POST(
  request: NextRequest,
  segmentData: { params: Promise<{ id: string }> }
): Promise<NextResponse<ApiCancelReminderResponse>> {
  const { id } = await segmentData.params;
  const reminderId = parseInt(id, 10);

  if (isNaN(reminderId)) {
    return NextResponse.json(
      {
        available: true,
        success: false,
        error: "Invalid reminder ID.",
      },
      {
        status: 400,
        headers: {
          "Cache-Control": "no-store, no-cache, must-revalidate",
        },
      }
    );
  }

  const result = await cancelBackendReminder(reminderId);

  return NextResponse.json(result, {
    status: 200,
    headers: {
      "Cache-Control": "no-store, no-cache, must-revalidate",
    },
  });
}
