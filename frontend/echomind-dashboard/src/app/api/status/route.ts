import { NextResponse } from "next/server";
import { fetchBackendStatus } from "@/lib/api/backend-client";
import { ApiStatusResponse } from "@/types/api";

export const dynamic = "force-dynamic";

export async function GET(): Promise<NextResponse<ApiStatusResponse>> {
  const result = await fetchBackendStatus();

  return NextResponse.json(result, {
    status: result.available ? 200 : 200,
    headers: {
      "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
    },
  });
}
