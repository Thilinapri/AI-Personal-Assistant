import { NextResponse } from "next/server";
import { fetchBackendReminders } from "@/lib/api/backend-client";
import { ApiRemindersResponse } from "@/types/api";

export const dynamic = "force-dynamic";

export async function GET(): Promise<NextResponse<ApiRemindersResponse>> {
  const result = await fetchBackendReminders();

  return NextResponse.json(result, {
    status: 200,
    headers: {
      "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
    },
  });
}
