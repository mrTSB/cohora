import { anthropic } from "@ai-sdk/anthropic";
import { appendResponseMessages, experimental_createMCPClient, streamText, ToolSet } from "ai";
import { getAllTools, MCPServer } from "@/lib/tools";
import { saveChat } from "@/lib/chat-store";
import { currentUser } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { JsonDB } from "@/lib/db";
import { Experimental_StdioMCPTransport as StdioMCPTransport } from "ai/mcp-stdio";

// Allow streaming responses up to 30 seconds
export const maxDuration = 30;

async function initializeMCPServer(server: MCPServer): Promise<ToolSet> {
  try {
    const mcpClient = await experimental_createMCPClient({
      transport: new StdioMCPTransport({
        command: server.command,
        args: server.args,
        env: server.env,
      }),
    });

    return mcpClient.tools();
  } catch (error) {
    console.error("Failed to initialize MCP server:", error);
    throw error;
  }
}

export async function POST(req: Request) {
  // get the last message from the client:
  const { messages, id } = await req.json();
  const user = await currentUser();
  if (!user) {
    redirect("/");
  }

  const db = new JsonDB();
  const servers = await db.getMcpServers(user.id);
  let allTools = { ...getAllTools };
  for (const server of Object.values(servers)) {
    console.log("New MCP Server", server.name);
    const serverTools = await initializeMCPServer(server);
    allTools = { ...allTools, ...serverTools };
  }

  const result = streamText({
    model: anthropic("claude-3-7-sonnet-latest"),
    messages,
    tools: allTools,
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
