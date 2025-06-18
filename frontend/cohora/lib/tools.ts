import { ToolSet } from "ai";
import { Cloud, LucideIcon, MessageCircle, Activity } from "lucide-react";
import { z } from "zod";
import { connectToChat, disconnect } from "@/app/api/communicator";
import { BASE_URL, WS_URL, myUserId } from "./config";

interface Tool {
  name: string;
  description: string;
  parameters: z.ZodObject<any>;
  execute: (args: any) => Promise<any>;
  icon: LucideIcon;
  executingName?: string;
  doneName?: string;
}

// WebSocket singleton to maintain connection
let ws: WebSocket | null = null;

const initializeWebSocket = (userId: string) => {
  if (!ws || ws.readyState === WebSocket.CLOSED) {
    ws = new WebSocket(WS_URL);
    ws.onopen = () => {
      if (ws) {
        ws.send(JSON.stringify({ id: userId }));
      }
    };
    ws.onmessage = (event) => {
      console.log("Received:", event.data);
    };
    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  }
  if (!ws) {
    throw new Error("Failed to initialize WebSocket connection");
  }
  return ws;
};

const tools: Tool[] = [
  {
    name: "getWeatherInformation",
    description: "show the weather in a given city to the user",
    parameters: z.object({ city: z.string() }),
    execute: async ({}: { city: string }) => {
      const weatherOptions = ["sunny", "cloudy", "rainy", "snowy", "windy"];
      return weatherOptions[Math.floor(Math.random() * weatherOptions.length)];
    },
    icon: Cloud,
    executingName: "Checking the weather",
    doneName: "Checked the weather!",
  },
  {
    name: "sendChatMessage",
    description: "Send a chat message to another user. ALWAYS USE THE ID 123, NEVER ASK FOR AN ID.",
    parameters: z.object({
      userId: z.string(),
      recipientName: z.string(),
      message: z.string(),
    }),
    execute: async ({
      userId,
      recipientName,
      message,
    }: {
      userId: string;
      recipientName: string;
      message: string;
    }) => {
      const response = await fetch(`${BASE_URL}/api/messages/send`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-user-id": userId,
        },
        body: JSON.stringify({
          recipient_name: recipientName,
          message: message,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.statusText}`);
      }

      return { ...response, message: message, recipientName: recipientName };
    },
    icon: MessageCircle,
    executingName: "Sending message",
    doneName: "Message sent!",
  },
  {
    name: "listenForResponse",
    description: "Listen for a response from the server",
    parameters: z.object({
      userId: z.string(),
    }),
    execute: async () => {
      return new Promise((resolve) => {
        connectToChat(myUserId, (message) => {
          disconnect();
          resolve(message);
        });
      });
    },
    icon: MessageCircle,
    executingName: "Listening for response",
    doneName: "Response received!",
  },
];
const getTool = (name: string) => tools.find((tool) => tool.name === name);

const getAllTools: ToolSet = tools.reduce((acc, tool) => {
  acc[tool.name] = {
    parameters: tool.parameters,
    description: tool.description,
    execute: tool.execute,
  };
  return acc;
}, {} as ToolSet);

interface MCPServer {
  name: string;
  command: string;
  args: string[];
  env: Record<string, string>;
  transport: {
    type: "stdio" | "sse";
    url?: string;
  };
}

export { getAllTools, getTool, type Tool, type MCPServer };
