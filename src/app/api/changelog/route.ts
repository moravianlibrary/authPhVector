import { NextResponse } from "next/server";
import { readFile } from "fs/promises";
import path from "path";

export async function GET() {
  const file = path.join(process.cwd(), "CHANGELOG.md");
  const content = await readFile(file, "utf-8");
  return NextResponse.json({ content });
}
