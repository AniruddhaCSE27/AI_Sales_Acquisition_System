import { NextResponse } from "next/server";

export function GET() {
  return NextResponse.json({
    status: "ok",
    service: "ai-sales-frontend",
    uptime: process.uptime(),
  });
}
