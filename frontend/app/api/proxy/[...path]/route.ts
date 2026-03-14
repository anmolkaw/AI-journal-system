import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = "http://127.0.0.1:8000";

type Context = {
  params: Promise<{ path: string[] }>;
};

async function forwardRequest(
  request: NextRequest,
  context: Context,
  method: string
) {
  try {
    const { path } = await context.params;
    const joinedPath = path.join("/");
    const targetUrl = `${BACKEND_URL}/api/${joinedPath}`;

    const body =
      method === "GET" || method === "DELETE" ? undefined : await request.text();

    const response = await fetch(targetUrl, {
      method,
      headers: {
        "Content-Type": "application/json",
      },
      body,
      cache: "no-store",
    });

    const text = await response.text();

    return new NextResponse(text, {
      status: response.status,
      headers: {
        "Content-Type":
          response.headers.get("Content-Type") || "application/json",
      },
    });
  } catch (error) {
    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : "Proxy request failed",
      },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest, context: Context) {
  return forwardRequest(request, context, "GET");
}

export async function POST(request: NextRequest, context: Context) {
  return forwardRequest(request, context, "POST");
}

export async function PUT(request: NextRequest, context: Context) {
  return forwardRequest(request, context, "PUT");
}

export async function PATCH(request: NextRequest, context: Context) {
  return forwardRequest(request, context, "PATCH");
}

export async function DELETE(request: NextRequest, context: Context) {
  return forwardRequest(request, context, "DELETE");
}