import { NextResponse } from "next/server";
import { fetchBackendMemoryHistory } from "@/lib/api/backend-client";
import { ApiMemoryHistoryResponse } from "@/types/api";

export const dynamic = "force-dynamic";

export async function GET(): Promise<NextResponse<ApiMemoryHistoryResponse>> {
  const result = await fetchBackendMemoryHistory();

  return NextResponse.json(result, {
    status: 200,
    headers: {
      "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
    },
  });
}
