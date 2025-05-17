import { JsonDB } from "@/lib/db";
import { MCPServer } from "@/lib/tools";
import { currentUser } from "@clerk/nextjs/server";

const db = new JsonDB();

export async function POST(req: Request) {
  const { name, command, args, env } = await req.json();
  console.log("Saving MCP Server ROUTE", name, command, args, env);
  const serverData: MCPServer = { name, command, args, env };
  const user = await currentUser();
  if (!user?.id) return;

  const serverId = crypto.randomUUID();
  await db.saveMcpServer(user.id, serverId, serverData);

  return new Response("MCPServer added", { status: 200 });
}
