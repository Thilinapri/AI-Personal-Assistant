import {
  NextResponse,
} from "next/server";

import {
  clearBackendMemories,
  fetchBackendMemories,
} from "@/lib/api/backend-client";

import {
  ApiMemoriesResponse,
  ApiMemoryMutationResponse,
} from "@/types/api";

export const dynamic =
  "force-dynamic";


export async function GET():
Promise<
  NextResponse<ApiMemoriesResponse>
> {
  const result =
    await fetchBackendMemories();

  return NextResponse.json(
    result,
    {
      status: 200,

      headers: {
        "Cache-Control":
          "no-store, no-cache, must-revalidate, proxy-revalidate",
      },
    },
  );
}


export async function DELETE():
Promise<
  NextResponse<ApiMemoryMutationResponse>
> {
  const result =
    await clearBackendMemories();

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