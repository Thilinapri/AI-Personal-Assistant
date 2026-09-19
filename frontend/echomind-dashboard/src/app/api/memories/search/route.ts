import { NextRequest, NextResponse } from "next/server";
import { fetchBackendMemorySearch } from "@/lib/api/backend-client";
import { ApiSearchResponse } from "@/types/api";

export const dynamic = "force-dynamic";

export async function GET(
  request: NextRequest
): Promise<NextResponse<ApiSearchResponse>> {
  const { searchParams } = new URL(request.url);
  const rawQuery = searchParams.get("q") ?? "";
  const trimmedQuery = rawQuery.trim();

  // Validate: do not dispatch to Flask if query is empty
  if (!trimmedQuery) {
    return NextResponse.json(
      {
        available: true,
        results: [],
        query: "",
      },
      {
        status: 200,
        headers: {
          "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
        },
      }
    );
  }

  const result = await fetchBackendMemorySearch(trimmedQuery);

  return NextResponse.json(result, {
    status: 200,
    headers: {
      "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
    },
  });
}
