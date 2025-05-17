import { anthropic } from "@ai-sdk/anthropic";
import { appendResponseMessages, streamText } from "ai";
import { getAllTools } from "@/lib/tools";
import { saveChat } from "@/lib/chat-store";

// Allow streaming responses up to 30 seconds
export const maxDuration = 30;

export async function POST(req: Request) {
  // get the last message from the client:
  const { messages, id } = await req.json();

  const result = streamText({
    model: anthropic("claude-3-7-sonnet-latest"),
    messages,
    tools: getAllTools,
    async onFinish({ response }) {
      await saveChat({
        id,
        messages: appendResponseMessages({
          messages,
          responseMessages: response.messages,
        }),
      });
    },
  });

  return result.toDataStreamResponse();
}
