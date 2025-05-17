import { anthropic } from "@ai-sdk/anthropic";
import { appendResponseMessages, streamText } from "ai";
import { getAllTools } from "@/lib/tools";
import { saveChat } from "@/lib/chat-store";
import { currentUser } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

// Allow streaming responses up to 30 seconds
export const maxDuration = 30;

export async function POST(req: Request) {
  // get the last message from the client:
  const { messages, id } = await req.json();
  const user = await currentUser();
  if (!user) {
    redirect("/");
  }

  const result = streamText({
    model: anthropic("claude-3-7-sonnet-latest"),
    messages,
    tools: getAllTools,
    async onFinish({ response }) {
      await saveChat({
        id,
        userId: user.id,
        messages: appendResponseMessages({
          messages,
          responseMessages: response.messages,
        }),
      });
    },
  });

  return result.toDataStreamResponse();
}
