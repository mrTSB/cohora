import { anthropic } from "@ai-sdk/anthropic";
import { streamText } from "ai";
import { getAllTools } from "@/lib/tools";

// Allow streaming responses up to 30 seconds
export const maxDuration = 30;

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: anthropic("claude-3-7-sonnet-latest"),
    messages,
    tools: getAllTools,
  });

  return result.toDataStreamResponse();
}
