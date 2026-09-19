import { NextResponse } from "next/server";
import { fetchBackendMemories } from "@/lib/api/backend-client";
import { ApiMemoriesResponse } from "@/types/api";

export const dynamic = "force-dynamic";

export async function GET(): Promise<NextResponse<ApiMemoriesResponse>> {
  const result = await fetchBackendMemories();

  return NextResponse.json(result, {
    status: 200,
    headers: {
      "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
    },
  });
}
